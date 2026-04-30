# pi0 / pi0.5 代码阅读笔记

以 [`src/openpi/models_pytorch/pi0_pytorch.py`](src/openpi/models_pytorch/pi0_pytorch.py) 为主线，把 pi0 的训练和推理路径、关键设计讲透，最后扩展到 pi0.5 的差异。

目标读者：看过论文、知道 Flow Matching 大致概念，但第一次读 pi0 代码的人。

---

## 0. 背景：pi0 做什么

pi0 是 Physical Intelligence 提出的 Vision-Language-Action (VLA) 模型，输入多路 RGB 图像 + 语言指令 + 机器人当前状态，输出未来一段时间的连续动作（action chunk，默认 50 步）。

核心训练范式：**Flow Matching** —— 不直接回归动作，而是学"从噪声到动作的速度场"，推理时用 Euler 积分从噪声解码出动作。

---

## 1. 整体架构：MoT (Mixture of Transformers) 设计

两套 Gemma 架构的 transformer 栈：

- **VLM backbone**（PaliGemma, 3B 预训练）—— 处理图像 + 语言
- **Action Expert**（300M 从头训）—— 处理 state + action + time

权重独立，但**共享 attention**：每层 attention 的 K/V 跨专家拼接，所以 action token 的 Q 能直接看到图像/语言的 K/V。

> **MoE vs MoT 辨析（一个值得抠的术语边界）**
>
> 论文原话写的是 *"analogous to a mixture of experts with two mixture elements"*，但严格来说这**不是 MoE**——MoE 的核心特征是 **router 在 token 级动态选 expert**（learned gate + top-k 路由）。pi0 没有 router，每个 token 走哪套权重由它的**类型**（图像/语言 vs state/action）**静态**决定，是 token 类型对 expert 的硬绑定。
>
> 这种"双 transformer 栈 + 共享 attention + 无 router + 类型静态路由"的结构，在后续工作 [Liang et al., *Mixture-of-Transformers: A Sparse and Scalable Architecture for Multi-Modal Foundation Models*, 2024](https://arxiv.org/abs/2411.04996) 里被正式定义为 **MoT (Mixture of Transformers)**。
>
> 所以 pi0 论文用 MoE 类比方便读者理解，但**实现就是 MoT**。后文为了和论文保持一致，"专家"一词偶尔仍会用，但请记得它实际是 MoT。

### 类初始化

```python
# pi0_pytorch.py:84-109
class PI0Pytorch(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.pi05 = config.pi05                       # pi0 / pi0.5 开关，决定后面一堆分支

        # 读取两套专家的 Gemma 配置（尺寸、层数、hidden_dim 等）
        paligemma_config = _gemma.get_config(config.paligemma_variant)          # 通常 gemma_2b
        action_expert_config = _gemma.get_config(config.action_expert_variant)  # 通常 gemma_300m

        # 构建双专家模型主体：PaliGemma（视觉语言）+ Gemma Expert（动作专家）
        self.paligemma_with_expert = PaliGemmaWithExpertModel(
            paligemma_config,
            action_expert_config,
            # use_adarms 长度 2，对应两套专家：VLM 不用 adaRMS，Action Expert 按 pi0.5 开关决定
            use_adarms=[False, True] if self.pi05 else [False, False],
            precision=config.dtype,                   # bf16 / float32
        )

        # 动作的输入/输出投影：action_dim ↔ expert_width（比如 32 ↔ 1024）
        self.action_in_proj = nn.Linear(config.action_dim, action_expert_config.width)
        self.action_out_proj = nn.Linear(action_expert_config.width, config.action_dim)

        if self.pi05:
            # pi0.5 用 adaRMS：时间单独走 MLP，生成条件信号注入每层 RMSNorm
            self.time_mlp_in = nn.Linear(action_expert_config.width, action_expert_config.width)
            self.time_mlp_out = nn.Linear(action_expert_config.width, action_expert_config.width)
        else:
            # pi0：
            # - state 单独成 token，需要 state_proj 把 state 向量投影到 expert_width
            # - 时间 concat 到 action（所以输入是 2*width），过 MLP 融合
            self.state_proj = nn.Linear(config.action_dim, action_expert_config.width)
            self.action_time_mlp_in = nn.Linear(2 * action_expert_config.width, action_expert_config.width)
            self.action_time_mlp_out = nn.Linear(action_expert_config.width, action_expert_config.width)
```

关键观察：
- `pi0` 分支有 `state_proj`（state 单独成 token）、`action_time_mlp_*`（时间 concat 到 action）
- `pi0.5` 分支有 `time_mlp_*`（时间走独立 MLP → adaRMS 条件）、**没有 state_proj**

---

## 2. Flow Matching 原理速览

### 公式（代码约定，和论文相反，见后文）

```
x_t = t·ε + (1-t)·A          # t=0 干净动作，t=1 纯噪声
u_t = ε - A                  # 真实速度场（不依赖 t，方向固定）
```

训练目标：让模型预测的速度场 `v_θ(x_t, obs, t) ≈ u_t`，loss 是 MSE。

推理：从纯噪声出发，Euler 积分 `x_{t+dt} = x_t + dt·v`（`dt = -1/num_steps` 负步长），10 步到 `t=0` 得到干净动作。

### 代码约定 vs 论文约定（重要坑）

论文：

```
A^τ = τ·A + (1-τ)·ε          # τ=0 噪声，τ=1 干净
u(A^τ|A) = A - ε
推理：τ 从 0 积分到 1
```

**代码把 t 的方向反了**：代码 `t=0` 干净，`t=1` 噪声。换元 `t_code = 1 - τ_paper` 可相互转换，数学完全等价。

为什么这么反着来？推理时 `t` 从 1 走到 0，方向和传统 diffusion denoising 一致，代码作者习惯这个方向。**看任何公式先问一句"此处 t=0 是哪端"**。

---

## 3. 训练路径：`forward`

入口：[pi0_pytorch.py:317-453](src/openpi/models_pytorch/pi0_pytorch.py#L317-L453)

每个 batch 调一次，算一次 Flow Matching loss。

### 完整流程（9 阶段）

#### ① 准备输入

```python
# forward 内（L347-L348）
# _preprocess_observation：归一化图像 + 从 Observation dataclass 里拆出各字段
# 返回一个 5 元组，分别对应：
#   images       —— list of [B, C, H, W]（多路相机）
#   img_masks    —— list of [B]（每路的有效性）
#   lang_tokens  —— [B, max_token_len]
#   lang_masks   —— [B, max_token_len]
#   state        —— [B, state_dim]
images, img_masks, lang_tokens, lang_masks, state = self._preprocess_observation(
    observation, train=True
)
```

`observation` 是 `Observation` dataclass：

```python
# model.py:83-100
@dataclass
class Observation:
    # 多路相机，key 是相机名（如 "base_0_rgb" / "left_wrist_0_rgb"），值是归一化到 [-1,1] 的 float32
    images: dict[str, Float[*b, h, w, c]]
    # 每路相机的可用性 mask——有些 setup 少相机，缺的视角补零图 + mask=False
    image_masks: dict[str, Bool[*b]]
    # 机器人低维本体感（关节角、夹爪开合等），LIBERO 是 8 维
    state: Float[*b, s]
    # 语言指令的 token id，PaliGemma tokenizer 编码，已 padding 到 max_token_len
    tokenized_prompt: Int[*b, l]
    # 语言 token 的 padding mask（True 表示有效 token，False 表示 padding）
    tokenized_prompt_mask: Bool[*b, l]
```

#### ② 采样 ε 和 t

```python
# pi0_pytorch.py:355-362
# 默认 None = 训练时内部随机采样；外部传入固定值可用于复现实验 / 单元测试
if noise is None:
    # 形状完全复制 actions.shape = [B, horizon=50, action_dim]，值独立采自标准正态
    noise = self.sample_noise(actions.shape, actions.device)   # ε ~ N(0,1)
if time is None:
    # 只采 B 个标量，每条样本一个 t（不是每个 action_horizon 步一个）
    time = self.sample_time(actions.shape[0], actions.device)  # t ~ Beta(1.5, 1)
```

- `noise` 形状同 `actions`：`[B, horizon=50, action_dim]`
- `time` 形状 `[B]`，每条样本一个 t
- **Beta(1.5, 1.0) 偏向大 t**（均值 0.6），代码约定下大 t 是噪声端，所以采样偏向"噪声多的难样本"

底层采样函数：

```python
# pi0_pytorch.py:173-185
def sample_noise(self, shape, device):
    # 标准正态，独立同分布
    return torch.normal(mean=0.0, std=1.0, size=shape, dtype=torch.float32, device=device)

def sample_time(self, bsize, device):
    # Beta(1.5, 1.0) 的 pdf = 1.5·x^0.5，在 [0,1] 上偏右（靠近 1）
    time_beta = sample_beta(1.5, 1.0, bsize, device)
    # 挤到 (0.001, 1]，避开 t=0 那一端的数值不稳定
    time = time_beta * 0.999 + 0.001
    return time.to(dtype=torch.float32, device=device)
```

#### ③ 构造 x_t 和 u_t

```python
# pi0_pytorch.py:368-373
# 从 [B] 扩到 [B,1,1]，和 [B, horizon, action_dim] 的 noise/actions 做逐元素相乘
time_expanded = time[:, None, None]

# x_t：干净动作 A 和噪声 ε 的线性插值
# t=0 -> 纯 A（干净），t=1 -> 纯 ε（噪声）；中间按比例混合
x_t = time_expanded * noise + (1 - time_expanded) * actions

# u_t：从 A 指向 ε 的方向（不依赖 t，常数向量！这是 FM 比 diffusion 好学的关键）
# 物理意义：如果模型学好了 v_θ ≈ u_t，推理时沿着它积分就能从 ε 走回 A
u_t = noise - actions
```

这就是 Flow Matching 的核心两行。

#### ④ 两套专家分别 embed

```python
# pi0_pytorch.py:386-391
prefix_embs, prefix_pad_masks, prefix_att_masks = self.embed_prefix(
    images, img_masks, lang_tokens, lang_masks
)
suffix_embs, suffix_pad_masks, suffix_att_masks, adarms_cond = self.embed_suffix(
    state, x_t, time
)
```

`embed_prefix`（图像 + 语言，送 VLM backbone）：

```python
# pi0_pytorch.py:187-236（简化后）
def embed_prefix(self, images, img_masks, lang_tokens, lang_masks):
    # 收集所有 prefix token 的 embedding、padding mask、块标志
    embs, pad_masks, att_masks = [], [], []

    # 多路相机逐个处理（LIBERO 里通常 2-3 路）
    for img, img_mask in zip(images, img_masks):
        # 每张图过 SigLIP vision encoder → 一堆 patch token（256 个 / 图）
        img_emb = self.paligemma_with_expert.embed_image(img)
        embs.append(img_emb)
        # img_mask 是 [B] 的相机有效性，广播成 [B, num_img_embs] 给每个 patch 一个 mask
        pad_masks.append(img_mask[:, None].expand(..., num_img_embs))
        # att_masks += [0]*N：所有图像 token 属于同一"块"，互相全注意力
        att_masks += [0] * num_img_embs

    # 语言 token 走 PaliGemma 的 embedding 层
    lang_emb = self.paligemma_with_expert.embed_language_tokens(lang_tokens)
    # PaliGemma 约定：embedding 后乘 sqrt(d)，是 Transformer 论文里的初始化稳定技巧
    lang_emb = lang_emb * math.sqrt(lang_emb.shape[-1])
    embs.append(lang_emb)
    pad_masks.append(lang_masks)
    # 语言 token 也全标 0，和图像属于同一块 → 图像和语言之间可以全注意力
    att_masks += [0] * num_lang_embs

    # 在 token 维（dim=1）concat 成 [B, N_img+N_lang, D]
    return torch.cat(embs, dim=1), torch.cat(pad_masks, dim=1), att_masks
```

`embed_suffix`（state + action + time，送 Action Expert）：

```python
# pi0_pytorch.py:238-315（pi0 分支简化）
def embed_suffix(self, state, noisy_actions, timestep):
    embs, pad_masks, att_masks = [], [], []

    # ═══ pi0 独有：state 成为单独一个 token ═══
    if not self.pi05:
        # state_proj: Linear(action_dim → expert_width)，把 8 维关节角投影到 1024 维
        state_emb = self.state_proj(state)                     # [B, D]
        # 升维成 [B, 1, D] —— 把它当成序列里只有 1 个 token
        embs.append(state_emb[:, None, :])
        pad_masks.append(torch.ones(bsize, 1, dtype=torch.bool, device=device))
        # att_masks = 1：state 开一个新块，和前面的图像/语言区分开
        att_masks += [1]

    # ═══ 时间编码：sin-cos 位置编码（类似 Transformer 经典 positional encoding）═══
    # min_period=4e-3, max_period=4.0 是专门为 t∈[0,1] 调的频率范围
    time_emb = create_sinusoidal_pos_embedding(timestep, ...)  # [B, D]

    # ═══ action 投影：把 [B, 50, action_dim] 投影到 [B, 50, expert_width] ═══
    action_emb = self.action_in_proj(noisy_actions)            # [B, 50, D]

    if not self.pi05:
        # ── pi0 做法：time 和 action concat 融合，只在输入端注入一次 ──
        # time 从 [B, D] 扩成 [B, 50, D]（50 个 action 每个都拼上相同的时间）
        time_emb = time_emb[:, None, :].expand_as(action_emb)
        # concat 后 channel 变 2D，再用 MLP 压回 D
        action_time_emb = torch.cat([action_emb, time_emb], dim=2)  # [B, 50, 2D]
        action_time_emb = self.action_time_mlp_out(
            F.silu(self.action_time_mlp_in(action_time_emb))         # swish 激活
        )
        # pi0 不用 adaRMS，返回 None
        adarms_cond = None
    else:
        # ── pi0.5 做法：time 单独走 MLP，不融进 action，而是作为 adaRMS 条件 ──
        time_emb = F.silu(self.time_mlp_out(F.silu(self.time_mlp_in(time_emb))))
        action_time_emb = action_emb                           # action 保持干净
        # adarms_cond 会在 PaliGemmaWithExpertModel.forward 里注入每层 RMSNorm
        adarms_cond = time_emb

    embs.append(action_time_emb)
    # att_masks = [1, 0, 0, ..., 0]：第一个 action 开新块，后续 49 个同块 → action 内部双向
    att_masks += [1] + [0] * (action_horizon - 1)

    return torch.cat(embs, dim=1), ..., adarms_cond
```

**pi0 的 suffix**：`[state_token, action_0, ..., action_49]` 共 51 token
**pi0.5 的 suffix**：`[action_0, ..., action_49]` 共 50 token（无 state token）

#### ⑤ 精度对齐

```python
# pi0_pytorch.py:393-398
# 检查 VLM 第一层的 q_proj 权重是不是 bf16（用它代表整个模型的精度）
if self.paligemma_with_expert.paligemma.language_model.layers[0].self_attn.q_proj.weight.dtype == torch.bfloat16:
    # 如果模型是 bf16，把输入 embedding 也转成 bf16，避免 matmul 时 dtype mismatch
    suffix_embs = suffix_embs.to(dtype=torch.bfloat16)
    prefix_embs = prefix_embs.to(dtype=torch.bfloat16)
```

bf16 训练时输入 embed 也要转 bf16，否则 dtype 不匹配。

#### ⑥ 拼接 + 构造 attention mask

```python
# pi0_pytorch.py:400-407
# 在 token 维（dim=1）把 prefix 和 suffix 的 mask 拼起来，形成整个序列的 mask
pad_masks = torch.cat([prefix_pad_masks, suffix_pad_masks], dim=1)   # [B, L]
att_masks = torch.cat([prefix_att_masks, suffix_att_masks], dim=1)   # [B, L]

# 把 1D 的块标志展开成 [B, L, L] 的真正 attention 矩阵（布尔值表示"能否 attend"）
att_2d_masks = make_att_2d_masks(pad_masks, att_masks)

# position_ids：按 pad_masks 累加减 1，padding 位置不占位置编码
# 例如 pad = [1,1,1,0,0,1]，cumsum-1 = [0,1,2,2,2,3]
position_ids = torch.cumsum(pad_masks, dim=1) - 1

# 布尔 mask 转成 transformer 期望的 4D 加性 mask：True→0.0，False→-inf
# shape: [B, L, L] → [B, 1, L, L]，1 那维是 num_heads 方向广播用的
att_2d_masks_4d = self._prepare_attention_masks_4d(att_2d_masks)
```

**1D `att_masks` 是"块分隔标志"**：
- `0`：和前一 token 同块
- `1`：新块开始，前面看不到自己

pi0 里 `att_masks` 长这样：
```
[0, 0, ..., 0,    # 图像 + 语言：全 0 = 一整块，互相全连接
 1,               # state：新块
 1, 0, 0, ..., 0] # action：新块 + 内部同块（双向）
```

`make_att_2d_masks`（[L52-81](src/openpi/models_pytorch/pi0_pytorch.py#L52-L81)）把它展开成 `[B, L, L]` bool 矩阵：

```python
def make_att_2d_masks(pad_masks, att_masks):
    cumsum = torch.cumsum(att_masks, dim=1)
    att_2d_masks = cumsum[:, None, :] <= cumsum[:, :, None]  # 关键一行
    pad_2d_masks = pad_masks[:, None, :] * pad_masks[:, :, None]
    return att_2d_masks & pad_2d_masks
```

效果就是 **prefix-LM** 结构：
- 图像/语言之间：全注意力
- 状态/动作 **能看** 图像/语言（条件输入）
- 图像/语言 **看不到** 状态/动作（防泄露）
- 动作内部：双向（论文说 "action expert uses a full bidirectional attention mask"）

#### ⑦ 联合 transformer forward

```python
# pi0_pytorch.py:409-420
# 包一层函数是为了配合 gradient checkpointing（显存换计算）
# 每次 forward() 都会重新 def 这个内部函数，开销可忽略
def forward_func(prefix_embs, suffix_embs, att_2d_masks_4d, position_ids, adarms_cond):
    # 返回值是 tuple：((VLM 输出, Action Expert 输出), past_kv)
    # 这里只取 suffix_out（Action Expert 的输出），VLM 输出训练时用不到（丢掉用 _）
    (_, suffix_out), _ = self.paligemma_with_expert.forward(
        attention_mask=att_2d_masks_4d,              # 共享 attention mask
        position_ids=position_ids,                   # 共享 position_ids
        past_key_values=None,                        # 训练从零开始算，没有历史 KV
        inputs_embeds=[prefix_embs, suffix_embs],    # [VLM 输入, Action Expert 输入]
        use_cache=False,                             # 训练不需要缓存 KV
        adarms_cond=[None, adarms_cond],             # VLM 不用 adaRMS，只给 Action Expert
    )
    return suffix_out

# _apply_checkpoint：开了 gradient checkpointing 就用 torch.utils.checkpoint 包裹
# 效果是 forward 时不存中间激活，backward 时重新跑一遍 forward 算梯度（省显存，慢一点）
suffix_out = self._apply_checkpoint(forward_func, ...)
```

`inputs_embeds` 是**长度 2 的 list**，分别送入两套专家。两者共享 attention mask 和 position_ids，但权重独立。

#### ⑧ 取 action 输出 + 投影

```python
# pi0_pytorch.py:432-443
# pi0 的 suffix_out 形状是 [B, 51, D]（state + 50 action），只要后 50 个
# pi0.5 的 suffix_out 就是 [B, 50, D]，切片也不会报错（不影响）
suffix_out = suffix_out[:, -self.config.action_horizon :]

# bf16 数值精度可能不够表达 action 的小变化，投影前转成 float32 更稳
suffix_out = suffix_out.to(dtype=torch.float32)

def action_out_proj_func(suffix_out):
    # Linear: expert_width → action_dim（比如 1024 → 32）
    # 得到模型预测的速度场 v_θ
    return self.action_out_proj(suffix_out)

v_t = self._apply_checkpoint(action_out_proj_func, suffix_out)   # 同样支持 checkpoint
```

为什么取后 50 个？pi0 的 suffix 是 `[state, action×50]`，state token 的输出没用。

#### ⑨ Flow Matching loss

```python
# pi0_pytorch.py:452
# MSE(u_t, v_t)：让模型预测的速度逼近真实速度
# reduction="none" 返回逐元素 loss [B, 50, action_dim]
# 外部会根据 padding mask / 有效步数做 .mean() 或加权平均
return F.mse_loss(u_t, v_t, reduction="none")
```

`reduction="none"` 保留逐元素 loss，外部可以按 mask 加权或取均值。

---

## 4. 推理路径：两阶段设计

入口：[pi0_pytorch.py:455-497](src/openpi/models_pytorch/pi0_pytorch.py#L455-L497) 的 `sample_actions`，核心循环调用 [denoise_step](src/openpi/models_pytorch/pi0_pytorch.py#L499-L543)。

### 关键观察：VLM 输出全程不变

推理时 observation（图像 + 语言）在 10 次 Euler 步里**完全不变**，唯一变化的是 `x_t` 和 `t`。所以 VLM 算一次就够，后面 10 次去噪复用其 K/V cache。

### 阶段 1：VLM 预热（只跑一次）

```python
# pi0_pytorch.py:462-476
# embed prefix（和训练时一样的 embed_prefix，没变）
prefix_embs, prefix_pad_masks, prefix_att_masks = self.embed_prefix(...)

# 构造 prefix 内部的 attention mask（只包含图像/语言之间的关系）
prefix_att_2d_masks = make_att_2d_masks(prefix_pad_masks, prefix_att_masks)
prefix_position_ids = torch.cumsum(prefix_pad_masks, dim=1) - 1
prefix_att_2d_masks_4d = self._prepare_attention_masks_4d(prefix_att_2d_masks)

# 关键一步：只跑 VLM，把每层的 K/V 算出来存进 past_key_values
# 返回的 _ 是 VLM 输出（不用），past_key_values 是 18 层 × (K, V) 的嵌套 tuple
_, past_key_values = self.paligemma_with_expert.forward(
    attention_mask=prefix_att_2d_masks_4d,
    position_ids=prefix_position_ids,
    past_key_values=None,                  # 第一次调用，没有历史
    inputs_embeds=[prefix_embs, None],     # VLM 有输入；Action Expert 为 None 表示不跑
    use_cache=True,                        # 告诉模型：把 K/V 存下来
)
# 至此 past_key_values 里保存了 VLM 所有 18 层的 K/V，后续 10 次 denoise 复用
```

`inputs_embeds=[prefix_embs, None]` 里的 `None` 是"这个专家不要前向"的信号。`use_cache=True` 让模型把每层的 K/V 存进 `past_key_values`。

### 阶段 2：Euler 循环（10 次）

```python
# pi0_pytorch.py:478-496
# dt 是负的（默认 -0.1），让 time 从 1 一路递减到 0
# 注意这里的"负"方向：代码约定 t=1 是噪声，t=0 是干净；积分方向就是"去噪"
dt = -1.0 / num_steps
dt = torch.tensor(dt, dtype=torch.float32, device=device)

x_t = noise                                       # 从纯噪声出发（代码约定下 t=1 处）
time = torch.tensor(1.0, dtype=torch.float32, device=device)

# while time >= -dt/2：相当于跑 num_steps 次（用 -dt/2 避开浮点累加误差）
while time >= -dt / 2:
    # time 是标量，扩成 [B]，每个样本用同一个 t
    expanded_time = time.expand(bsize)
    # 调 denoise_step 得到当前 t 处的速度场预测 v_θ
    v_t = self.denoise_step(
        state, prefix_pad_masks, past_key_values, x_t, expanded_time,
    )
    # Euler 积分一步：x_{t+dt} = x_t + dt · v
    # dt 是负的，所以 time 减小，x_t 往干净方向走
    x_t = x_t + dt * v_t
    time += dt
return x_t                                        # time=0 时，x_t 就是干净动作
```

### `denoise_step` 每一步做什么

```python
# pi0_pytorch.py:499-543
def denoise_step(self, state, prefix_pad_masks, past_key_values, x_t, timestep):
    # 每次 Euler 步都要用新的 x_t 和 timestep 重新算一遍 suffix embedding
    # （state 本身不变，但 pi0 没单独缓存它，每次照常参与计算）
    suffix_embs, suffix_pad_masks, suffix_att_masks, adarms_cond = self.embed_suffix(
        state, x_t, timestep
    )

    # ═══ 构造 attention mask ═══
    # prefix 部分：suffix token 能"看到"所有 prefix token（条件输入）
    #   做法是把 prefix_pad_mask [B, prefix_len] 广播成 [B, suffix_len, prefix_len]
    prefix_pad_2d_masks = prefix_pad_masks[:, None, :].expand(batch_size, suffix_len, prefix_len)
    # suffix 内部：正常按块标志构造（state 新块，action 新块且内部双向）
    suffix_att_2d_masks = make_att_2d_masks(suffix_pad_masks, suffix_att_masks)
    # 沿 key 维拼接：[B, suffix_len, prefix_len + suffix_len]
    full_att_2d_masks = torch.cat([prefix_pad_2d_masks, suffix_att_2d_masks], dim=2)

    # ═══ position_ids 接在 prefix 后面 ═══
    # 每条样本 prefix 的真实长度（排除 padding）
    prefix_offsets = torch.sum(prefix_pad_masks, dim=-1)[:, None]
    # suffix 的位置 = prefix 长度 + suffix 内部的 cumsum
    position_ids = prefix_offsets + torch.cumsum(suffix_pad_masks, dim=1) - 1

    full_att_2d_masks_4d = self._prepare_attention_masks_4d(full_att_2d_masks)

    # ═══ 只跑 Action Expert，VLM 的 K/V 从 past_key_values 取 ═══
    outputs_embeds, _ = self.paligemma_with_expert.forward(
        attention_mask=full_att_2d_masks_4d,
        position_ids=position_ids,
        past_key_values=past_key_values,      # ← 这就是阶段 1 存下的 VLM KV
        inputs_embeds=[None, suffix_embs],    # ← VLM 不跑，只跑 Action Expert
        use_cache=False,                      # 不需要继续缓存（每步 suffix 都变）
        adarms_cond=[None, adarms_cond],      # pi0.5 时 adarms_cond 非 None
    )

    # outputs_embeds 是 [VLM_out, Expert_out]，VLM_out 是 None（没跑），取 [1]
    suffix_out = outputs_embeds[1]
    suffix_out = suffix_out[:, -self.config.action_horizon :]   # 取 action 部分
    suffix_out = suffix_out.to(dtype=torch.float32)
    # 投影得到预测的速度 v_θ，返回给外层 Euler 循环
    return self.action_out_proj(suffix_out)
```

**关键**：`inputs_embeds=[None, suffix_embs]` + `past_key_values=past_key_values` 的组合——只算 Action Expert，attention 里 VLM 部分的 K/V 从 cache 取。

### 三处 `inputs_embeds` 对比

| 位置 | 调用 | 目的 |
|------|------|------|
| 训练 [L415](src/openpi/models_pytorch/pi0_pytorch.py#L415) | `[prefix, suffix]` | 一次算完 loss |
| 推理预热 [L465](src/openpi/models_pytorch/pi0_pytorch.py#L465) | `[prefix, None]` + `use_cache=True` | 只跑 VLM，存 K/V |
| 推理循环 [L521](src/openpi/models_pytorch/pi0_pytorch.py#L521) | `[None, suffix]` + `past_key_values=cached` | 只跑 Action Expert，复用缓存 |

### 性能收益

粗估（VLM 占 ~70-80%，Action Expert 占 ~20-30%）：
- 不优化：10 × (VLM + Expert) ≈ **1000%**
- 现在：1 × VLM + 10 × Expert ≈ **280%**
- 省约 **3.5×**

---

## 5. 训练 vs 推理：一张表对比

| 特征 | 训练 `forward` | 推理 `sample_actions` |
|------|--------------|---------------------|
| 外层循环 | 无 | 10 次 Euler |
| VLM 跑几次 | 1 | 1（预热）|
| Action Expert 跑几次 | 1 | 10 |
| KV cache | 不用 | 用（prefix 缓存） |
| 最终输出 | MSE loss | 干净动作 chunk |
| `t` / ε | 随机采 1 个 | `t` 从 1 走到 0 积分 |

---

## 6. Attention Mask 机制详解

所有 mask 逻辑都在 `make_att_2d_masks`（[L52-81](src/openpi/models_pytorch/pi0_pytorch.py#L52-L81)）里：

```python
# att_masks 是 1D 的块标志 [B, L]，值是 0 或 1
# cumsum 把它累加 → 每个位置得到一个"块号"
# 例如 att_masks = [0, 0, 1, 0, 0, 1, 0]
#      cumsum    = [0, 0, 1, 1, 1, 2, 2]   → 位置 0-1 是块 0，2-4 是块 1，5-6 是块 2
cumsum = torch.cumsum(att_masks, dim=1)

# 广播比较：cumsum[:, None, :] 形状 [B, 1, L]（作为 key 维）
#          cumsum[:, :, None] 形状 [B, L, 1]（作为 query 维）
# att_2d_masks[b, i, j] = True ↔ cumsum[i] >= cumsum[j]
# 含义："query 位置 i 的块号 >= key 位置 j 的块号" → 能 attend
# 所以 query 能看到所有块号 <= 自己的 key（同块或更早的块）
att_2d_masks = cumsum[:, None, :] <= cumsum[:, :, None]
```

**直觉理解**：`cumsum` 给每个 token 一个"块号"。`cumsum[i] <= cumsum[j]` 意味着"位置 j 能看到位置 i"——即 j 的块号大于等于 i 的块号。

配合 pi0 的 `att_masks = [0,...,0, 1, 1,0,...,0]`：

| token | att_masks | cumsum | 属于哪块 |
|-------|----------|--------|---------|
| image + lang | 0 | 0 | 块 0 |
| state | 1 | 1 | 块 1 |
| action_0 | 1 | 2 | 块 2 |
| action_1..49 | 0 | 2 | 块 2 |

所以：
- 块 0（图像/语言）只能看块号 ≤ 0 的 → 只看自己
- 块 1（state）能看块号 ≤ 1 → 图像/语言 + state
- 块 2（action）能看块号 ≤ 2 → 全部（但 action 内部都是块 2，所以内部双向）

这就是 prefix-LM + action 双向的 mask 设计。

---

## 7. pi0.5 的差异

从 `pi0_config.py` 的注释：

```python
# Pi05 has two differences from Pi0:
# - the state input is part of the discrete language tokens rather than a continuous input
# - the action expert uses adaRMSNorm to inject the flow matching timestep
pi05: bool = False
```

### 差异 1：adaRMS 注入时间

**pi0 的做法**：时间 embedding concat 到 action token 输入端，过一次 MLP 融合（只在输入层作用一次）。

**pi0.5 的做法**：时间走独立 MLP 生成 `adarms_cond`，在**每一层 RMSNorm** 都注入。

核心实现 [modeling_gemma.py:73-104](src/openpi/models_pytorch/transformers_replace/models/gemma/modeling_gemma.py#L73-L104)：

```python
def forward(self, x, cond=None):
    # 先做标准 RMS 归一化：y = x / sqrt(mean(x²))
    normed_inputs = self._norm(x)

    # 没有 cond（pi0）或这一层不支持 adaRMS（VLM 层）→ 走普通 RMSNorm
    if cond is None or self.dense is None:
        # 普通 RMSNorm：乘一个可学习的 weight（每层一个固定参数）
        return normed_inputs * (1.0 + self.weight), None

    # ═══ adaRMS：用条件信号动态生成 scale / shift / gate ═══
    # cond 形状 [B, cond_dim]，dense 是 Linear(cond_dim → 3·dim)
    # 输出拆成三份：scale、shift、gate
    modulation = self.dense(cond)
    scale, shift, gate = torch.chunk(modulation, 3, dim=-1)

    # 条件化归一化：不再是固定的 weight，而是 (1 + scale(cond))
    # 并且多了一个 shift(cond) 偏移项
    normed_inputs = normed_inputs * (1 + scale) + shift

    # gate 返回给外层，用来调制残差连接（见下方 _gated_residual）
    return normed_inputs, gate
```

残差连接也被 `gate` 控制（类似 LayerScale）：

```python
# pi0_pytorch.py:378（实际在 gemma 层里）
# 普通残差：h = residual + attn_out
# gated 残差：h = residual + gate(cond) · attn_out
# gate 近 0 时相当于"跳过这一层的贡献"，让模型自己学习每层贡献多少
hidden_states = _gated_residual(residual, hidden_states, gate)
```

思想来自 **DiT（Diffusion Transformer）**：时间条件在每层分布式注入，比输入端一次 concat 更细腻。

### 差异 2：state 塞进 prompt（离散化）

pi0.5 **完全去掉 state token**，改成把 state 离散化后拼进语言 prompt。

实现在 [tokenizer.py:22-48](src/openpi/models/tokenizer.py#L22-L48)：

```python
def tokenize(self, prompt: str, state: np.ndarray | None = None):
    # 清洗 prompt：去前后空白，换掉下划线和换行
    cleaned_text = prompt.strip().replace("_", " ").replace("\n", " ")

    if state is not None:
        # ═══ pi0.5 路径：state 进 prompt ═══
        # np.digitize：把每维 state 值分到 256 个 bin 里
        # bins=np.linspace(-1, 1, 257)[:-1] 生成 256 个左边界（-1.000, -0.992, ...）
        # -1 是因为 digitize 默认从 1 开始编号，减 1 让 bin 编号从 0-255
        discretized_state = np.digitize(state, bins=np.linspace(-1, 1, 256 + 1)[:-1]) - 1

        # 把离散 bin 号拼成空格分隔的字符串，如 "145 73 224 12 ..."
        state_str = " ".join(map(str, discretized_state))

        # 完整 prompt：包含任务描述 + state 数字串 + Action 提示
        # 示例 "Task: pick the apple, State: 145 73 224 12 67 89 143 201;\nAction: "
        full_prompt = f"Task: {cleaned_text}, State: {state_str};\nAction: "

        # 整个字符串过 SentencePiece tokenizer，加 BOS（<bos> 起始 token）
        tokens = self._tokenizer.encode(full_prompt, add_bos=True)
    else:
        # ═══ pi0 路径：state 不在 prompt 里，留给 Action Expert 处理 ═══
        # "\n" 作为 "start of answer" 分隔符单独编码
        tokens = self._tokenizer.encode(cleaned_text, add_bos=True) + self._tokenizer.encode("\n")
```

过程：
1. state 归一化到 `[-1, 1]` 后，`np.digitize` 分到 256 个 bin
2. 拼字符串：`"Task: pick the apple, State: 145 73 224 ...;\nAction: "`
3. 整个字符串过 PaliGemma tokenizer → token id

**配套变化**：`max_token_len` 从 48 增加到 200（state 字符串化后占很多位置）。

### 差异 3：`embed_suffix` 简化

pi0.5 分支直接跳过 state 相关代码 [pi0_pytorch.py:244](src/openpi/models_pytorch/pi0_pytorch.py#L244)：

```python
if not self.pi05:   # ← pi0.5 时这个 if 为 False，整段直接跳过
    # 以下只在 pi0 时执行：把 state 向量投影成一个 token
    state_emb = self.state_proj(state)
    embs.append(state_emb[:, None, :])
    ...
    att_masks += [1]
# pi0.5 没有 state token，suffix 里只有 50 个 action token
```

pi0.5 的 suffix 里**只有 50 个 action token**，没有 state token。

### 这些改动的好处

#### 1. VLM 直接理解 state
state 和图像、语言在 prefix 全注意力块里自由交互，VLM 的 18 层视觉语言处理全部作用于 state。

#### 2. KV cache 覆盖 state
state 属于 prefix，所以推理时 `[prefix_embs, None]` 预热一次就把 state 的 K/V 一并缓存。**彻底消除 pi0 里"state 在 10 次 denoise_step 被重复计算"的浪费**。

#### 3. 架构更统一
- pi0：图像 token + 语言 token + state 向量 + action 向量 → 4 种东西
- pi0.5：prompt 文本 token + action 向量 → 2 种

### 离散化 256 bin 够用吗

- 机械臂关节精度一般 0.1-1°，范围约 360°
- 256 bin ≈ 1.4° 每 bin
- 足够大部分任务；精密装配可能有影响，但 **action 输出仍然是连续的**（由 Action Expert 输出），所以最终控制精度不受影响

### 一张表对照

| 特征 | pi0 | pi0.5 |
|------|-----|-------|
| state 形式 | 连续向量 → state_proj → 1 个 token | 离散化 256 bin → 文本 → 若干 token |
| state 位置 | Action Expert 的 suffix | VLM backbone 的 prompt |
| state 重复计算 | 推理时 10 次 denoise 每次重算 | 享受 KV cache |
| 时间条件 | concat 到 action → MLP，输入端一次 | adaRMS，每层注入 |
| suffix 长度 | 51 (state + 50 action) | 50 (只有 action) |
| `max_token_len` | 48 | 200 |

---

## 8. 读代码的心得

1. **看签名比看函数体先开始**：`def forward(self, observation, actions, noise=None, time=None)` 一眼就知道输入输出是什么，避免读到中间被"noise 哪来的"卡住
2. **公式约定看代码最稳**：论文和代码的 `τ` / `t` 方向可以完全相反，自己代入 `t=0` 和 `t=1` 验证一次立刻清楚
3. **两套专家要先分清楚再合并**：先各看 `embed_prefix` / `embed_suffix`，再看 `torch.cat` + attention mask 怎么把它们粘起来
4. **训练和推理分开读**：同一个模型类有两条完全不同的代码路径（一个算 loss，一个跑 Euler），混着读会崩溃
5. **`inputs_embeds=[A, None]` 这种设计**：为 KV cache 场景留的接口，看到 `None` 就要想到"这个专家不前向"
6. **attention mask 的 1D 块标志 → 2D 矩阵**：`make_att_2d_masks` 的 `cumsum` 比较是理解 prefix-LM 的钥匙

---

## 9. 可以继续深入的方向

- [ ] `PaliGemmaWithExpertModel.forward`：两套专家共享 attention 在底层怎么实现（K/V 跨专家拼接）
- [ ] `embed_prefix` 里的 SigLIP 图像编码细节
- [ ] adaRMS 的 gate 在残差连接里的具体作用（`_gated_residual`）
- [ ] 训练数据 pipeline：`observation` / `actions` 从 LeRobot dataset 到 tensor 的完整路径
- [ ] pi0-FAST：另一种 action tokenization 方案（autoregressive + discrete）

---

## 附录：关键文件位置

- 主模型：[src/openpi/models_pytorch/pi0_pytorch.py](src/openpi/models_pytorch/pi0_pytorch.py)
- 两套专家 transformer 实现：[src/openpi/models_pytorch/gemma_pytorch.py](src/openpi/models_pytorch/gemma_pytorch.py)
- adaRMS 和 Gemma 层：[src/openpi/models_pytorch/transformers_replace/models/gemma/modeling_gemma.py](src/openpi/models_pytorch/transformers_replace/models/gemma/modeling_gemma.py)
- 数据结构：[src/openpi/models/model.py](src/openpi/models/model.py)
- Tokenizer：[src/openpi/models/tokenizer.py](src/openpi/models/tokenizer.py)
- Config：[src/openpi/models/pi0_config.py](src/openpi/models/pi0_config.py)
- 观测预处理：[src/openpi/models_pytorch/preprocessing_pytorch.py](src/openpi/models_pytorch/preprocessing_pytorch.py)
