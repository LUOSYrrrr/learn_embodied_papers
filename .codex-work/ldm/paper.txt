                                                         High-Resolution Image Synthesis with Latent Diffusion Models

                                          Robin Rombach1 *                    Andreas Blattmann1 ∗           Dominik Lorenz1                       Patrick Esser                            Björn Ommer1
                                                                1
                                                                    Ludwig Maximilian University of Munich & IWR, Heidelberg University, Germany                        Runway ML
                                                                           https://github.com/CompVis/latent-diffusion


                                                                                                                                       ours (f = 4)           DALL-E (f = 8)          VQGAN (f = 16)
                                                                       Abstract                                        Input       PSNR: 27.4 R-FID: 0.58   PSNR: 22.8 R-FID: 32.01   PSNR: 19.9 R-FID: 4.98



                                            By decomposing the image formation process into a se-




arXiv:2112.10752v2 [cs.CV] 13 Apr 2022
                                         quential application of denoising autoencoders, diffusion
                                         models (DMs) achieve state-of-the-art synthesis results on
                                         image data and beyond. Additionally, their formulation al-
                                         lows for a guiding mechanism to control the image gen-
                                         eration process without retraining. However, since these
                                         models typically operate directly in pixel space, optimiza-
                                         tion of powerful DMs often consumes hundreds of GPU
                                         days and inference is expensive due to sequential evalu-
                                         ations. To enable DM training on limited computational
                                         resources while retaining their quality and flexibility, we             Figure 1. Boosting the upper bound on achievable quality with
                                                                                                                 less agressive downsampling. Since diffusion models offer excel-
                                         apply them in the latent space of powerful pretrained au-
                                                                                                                 lent inductive biases for spatial data, we do not need the heavy spa-
                                         toencoders. In contrast to previous work, training diffusion            tial downsampling of related generative models in latent space, but
                                         models on such a representation allows for the first time               can still greatly reduce the dimensionality of the data via suitable
                                         to reach a near-optimal point between complexity reduc-                 autoencoding models, see Sec. 3. Images are from the DIV2K [1]
                                         tion and detail preservation, greatly boosting visual fidelity.         validation set, evaluated at 5122 px. We denote the spatial down-
                                         By introducing cross-attention layers into the model archi-             sampling factor by f . Reconstruction FIDs [29] and PSNR are
                                         tecture, we turn diffusion models into powerful and flexi-              calculated on ImageNet-val. [12]; see also Tab. 8.
                                         ble generators for general conditioning inputs such as text
                                         or bounding boxes and high-resolution synthesis becomes                 results in image synthesis [30,85] and beyond [7,45,48,57],
                                         possible in a convolutional manner. Our latent diffusion                and define the state-of-the-art in class-conditional image
                                         models (LDMs) achieve new state-of-the-art scores for im-               synthesis [15,31] and super-resolution [72]. Moreover, even
                                         age inpainting and class-conditional image synthesis and                unconditional DMs can readily be applied to tasks such
                                         highly competitive performance on various tasks, includ-                as inpainting and colorization [85] or stroke-based syn-
                                         ing text-to-image synthesis, unconditional image generation             thesis [53], in contrast to other types of generative mod-
                                         and super-resolution, while significantly reducing computa-             els [19, 46, 69]. Being likelihood-based models, they do not
                                         tional requirements compared to pixel-based DMs.                        exhibit mode-collapse and training instabilities as GANs
                                                                                                                 and, by heavily exploiting parameter sharing, they can
                                         1. Introduction                                                         model highly complex distributions of natural images with-
                                             Image synthesis is one of the computer vision fields with           out involving billions of parameters as in AR models [67].
                                         the most spectacular recent development, but also among                 Democratizing High-Resolution Image Synthesis DMs
                                         those with the greatest computational demands. Espe-                    belong to the class of likelihood-based models, whose
                                         cially high-resolution synthesis of complex, natural scenes             mode-covering behavior makes them prone to spend ex-
                                         is presently dominated by scaling up likelihood-based mod-              cessive amounts of capacity (and thus compute resources)
                                         els, potentially containing billions of parameters in autore-           on modeling imperceptible details of the data [16, 73]. Al-
                                         gressive (AR) transformers [66,67]. In contrast, the promis-            though the reweighted variational objective [30] aims to ad-
                                         ing results of GANs [3, 27, 40] have been revealed to be                dress this by undersampling the initial denoising steps, DMs
                                         mostly confined to data with comparably limited variability             are still computationally demanding, since training and
                                         as their adversarial learning procedure does not easily scale           evaluating such a model requires repeated function evalu-
                                         to modeling complex, multi-modal distributions. Recently,               ations (and gradient computations) in the high-dimensional
                                         diffusion models [82], which are built from a hierarchy of              space of RGB images. As an example, training the most
                                         denoising autoencoders, have shown to achieve impressive                powerful DMs often takes hundreds of GPU days (e.g. 150 -
                                                                                                                 1000 V100 days in [15]) and repeated evaluations on a noisy
                                           * The first two authors contributed equally to this work.             version of the input space render also inference expensive,
                                                                                                             1
so that producing 50k samples takes approximately 5 days
[15] on a single A100 GPU. This has two consequences for
the research community and users in general: Firstly, train-
ing such a model requires massive computational resources
only available to a small fraction of the field, and leaves a
huge carbon footprint [65, 86]. Secondly, evaluating an al-
ready trained model is also expensive in time and memory,
since the same model architecture must run sequentially for
a large number of steps (e.g. 25 - 1000 steps in [15]).
    To increase the accessibility of this powerful model class
and at the same time reduce its significant resource con-
sumption, a method is needed that reduces the computa-
tional complexity for both training and sampling. Reducing
the computational demands of DMs without impairing their               Figure 2. Illustrating perceptual and semantic compression: Most
performance is, therefore, key to enhance their accessibility.         bits of a digital image correspond to imperceptible details. While
                                                                       DMs allow to suppress this semantically meaningless information
Departure to Latent Space Our approach starts with                     by minimizing the responsible loss term, gradients (during train-
the analysis of already trained diffusion models in pixel              ing) and the neural network backbone (training and inference) still
space: Fig. 2 shows the rate-distortion trade-off of a trained         need to be evaluated on all pixels, leading to superfluous compu-
model. As with any likelihood-based model, learning can                tations and unnecessarily expensive optimization and inference.
be roughly divided into two stages: First is a perceptual              We propose latent diffusion models (LDMs) as an effective gener-
compression stage which removes high-frequency details                 ative model and a separate mild compression stage that only elim-
but still learns little semantic variation. In the second stage,       inates imperceptible details. Data and images from [30].
the actual generative model learns the semantic and concep-
tual composition of the data (semantic compression). We                applied to high-resolution synthesis of megapixel images.
thus aim to first find a perceptually equivalent, but compu-               (ii) We achieve competitive performance on multiple
tationally more suitable space, in which we will train diffu-          tasks (unconditional image synthesis, inpainting, stochastic
sion models for high-resolution image synthesis.                       super-resolution) and datasets while significantly lowering
    Following common practice [11, 23, 66, 67, 96], we sep-            computational costs. Compared to pixel-based diffusion ap-
arate training into two distinct phases: First, we train               proaches, we also significantly decrease inference costs.
an autoencoder which provides a lower-dimensional (and                     (iii) We show that, in contrast to previous work [93]
thereby efficient) representational space which is perceptu-           which learns both an encoder/decoder architecture and a
ally equivalent to the data space. Importantly, and in con-            score-based prior simultaneously, our approach does not re-
trast to previous work [23,66], we do not need to rely on ex-          quire a delicate weighting of reconstruction and generative
cessive spatial compression, as we train DMs in the learned            abilities. This ensures extremely faithful reconstructions
latent space, which exhibits better scaling properties with            and requires very little regularization of the latent space.
respect to the spatial dimensionality. The reduced complex-                (iv) We find that for densely conditioned tasks such
ity also provides efficient image generation from the latent           as super-resolution, inpainting and semantic synthesis, our
space with a single network pass. We dub the resulting                 model can be applied in a convolutional fashion and render
model class Latent Diffusion Models (LDMs).                            large, consistent images of ∼ 10242 px.
    A notable advantage of this approach is that we need to                (v) Moreover, we design a general-purpose conditioning
train the universal autoencoding stage only once and can               mechanism based on cross-attention, enabling multi-modal
therefore reuse it for multiple DM trainings or to explore             training. We use it to train class-conditional, text-to-image
possibly completely different tasks [81]. This enables effi-           and layout-to-image models.
cient exploration of a large number of diffusion models for                (vi) Finally, we release pretrained latent diffusion
various image-to-image and text-to-image tasks. For the lat-           and autoencoding models at https : / / github .
ter, we design an architecture that connects transformers to           com/CompVis/latent-diffusion which might be
the DM’s UNet backbone [71] and enables arbitrary types                reusable for a various tasks besides training of DMs [81].
of token-based conditioning mechanisms, see Sec. 3.3.
    In sum, our work makes the following contributions:                2. Related Work
    (i) In contrast to purely transformer-based approaches                Generative Models for Image Synthesis The high di-
[23, 66], our method scales more graceful to higher dimen-             mensional nature of images presents distinct challenges
sional data and can thus (a) work on a compression level               to generative modeling. Generative Adversarial Networks
which provides more faithful and detailed reconstructions              (GAN) [27] allow for efficient sampling of high resolution
than previous work (see Fig. 1) and (b) can be efficiently             images with good perceptual quality [3, 42], but are diffi-
                                                                   2
cult to optimize [2, 28, 54] and struggle to capture the full         proaches and less compression comes at the price of high
data distribution [55]. In contrast, likelihood-based meth-           computational cost [23, 66]. Our work prevents such trade-
ods emphasize good density estimation which renders op-               offs, as our proposed LDMs scale more gently to higher
timization more well-behaved. Variational autoencoders                dimensional latent spaces due to their convolutional back-
(VAE) [46] and flow-based models [18, 19] enable efficient            bone. Thus, we are free to choose the level of compression
synthesis of high resolution images [9, 44, 92], but sam-             which optimally mediates between learning a powerful first
ple quality is not on par with GANs. While autoregressive             stage, without leaving too much perceptual compression up
models (ARM) [6, 10, 94, 95] achieve strong performance               to the generative diffusion model while guaranteeing high-
in density estimation, computationally demanding architec-            fidelity reconstructions (see Fig. 1).
tures [97] and a sequential sampling process limit them to               While approaches to jointly [93] or separately [80] learn
low resolution images. Because pixel based representations            an encoding/decoding model together with a score-based
of images contain barely perceptible, high-frequency de-              prior exist, the former still require a difficult weighting be-
tails [16,73], maximum-likelihood training spends a dispro-           tween reconstruction and generative capabilities [11] and
portionate amount of capacity on modeling them, resulting             are outperformed by our approach (Sec. 4), and the latter
in long training times. To scale to higher resolutions, several       focus on highly structured images such as human faces.
two-stage approaches [23,67,101,103] use ARMs to model
a compressed latent image space instead of raw pixels.                3. Method
    Recently, Diffusion Probabilistic Models (DM) [82],                  To lower the computational demands of training diffu-
have achieved state-of-the-art results in density estimation          sion models towards high-resolution image synthesis, we
[45] as well as in sample quality [15]. The generative power          observe that although diffusion models allow to ignore
of these models stems from a natural fit to the inductive bi-         perceptually irrelevant details by undersampling the corre-
ases of image-like data when their underlying neural back-            sponding loss terms [30], they still require costly function
bone is implemented as a UNet [15, 30, 71, 85]. The best              evaluations in pixel space, which causes huge demands in
synthesis quality is usually achieved when a reweighted ob-           computation time and energy resources.
jective [30] is used for training. In this case, the DM corre-           We propose to circumvent this drawback by introducing
sponds to a lossy compressor and allow to trade image qual-           an explicit separation of the compressive from the genera-
ity for compression capabilities. Evaluating and optimizing           tive learning phase (see Fig. 2). To achieve this, we utilize
these models in pixel space, however, has the downside of             an autoencoding model which learns a space that is percep-
low inference speed and very high training costs. While               tually equivalent to the image space, but offers significantly
the former can be partially adressed by advanced sampling             reduced computational complexity.
strategies [47, 75, 84] and hierarchical approaches [31, 93],            Such an approach offers several advantages: (i) By leav-
training on high-resolution image data always requires to             ing the high-dimensional image space, we obtain DMs
calculate expensive gradients. We adress both drawbacks               which are computationally much more efficient because
with our proposed LDMs, which work on a compressed la-                sampling is performed on a low-dimensional space. (ii) We
tent space of lower dimensionality. This renders training             exploit the inductive bias of DMs inherited from their UNet
computationally cheaper and speeds up inference with al-              architecture [71], which makes them particularly effective
most no reduction in synthesis quality (see Fig. 1).                  for data with spatial structure and therefore alleviates the
   Two-Stage Image Synthesis To mitigate the shortcom-                need for aggressive, quality-reducing compression levels as
ings of individual generative approaches, a lot of research           required by previous approaches [23, 66]. (iii) Finally, we
[11, 23, 67, 70, 101, 103] has gone into combining the                obtain general-purpose compression models whose latent
strengths of different methods into more efficient and per-           space can be used to train multiple generative models and
formant models via a two stage approach. VQ-VAEs [67,                 which can also be utilized for other downstream applica-
101] use autoregressive models to learn an expressive prior           tions such as single-image CLIP-guided synthesis [25].
over a discretized latent space. [66] extend this approach to
text-to-image generation by learning a joint distributation           3.1. Perceptual Image Compression
over discretized image and text representations. More gen-               Our perceptual compression model is based on previous
erally, [70] uses conditionally invertible networks to pro-           work [23] and consists of an autoencoder trained by com-
vide a generic transfer between latent spaces of diverse do-          bination of a perceptual loss [106] and a patch-based [33]
mains. Different from VQ-VAEs, VQGANs [23, 103] em-                   adversarial objective [20, 23, 103]. This ensures that the re-
ploy a first stage with an adversarial and perceptual objec-          constructions are confined to the image manifold by enforc-
tive to scale autoregressive transformers to larger images.           ing local realism and avoids bluriness introduced by relying
However, the high compression rates required for feasible             solely on pixel-space losses such as L2 or L1 objectives.
ARM training, which introduces billions of trainable pa-                 More precisely, given an image x ∈ RH×W ×3 in RGB
rameters [23, 66], limit the overall performance of such ap-          space, the encoder E encodes x into a latent representa-
                                                                  3
                                                                                                           Latent Space
tion z = E(x), and the decoder D reconstructs the im-                                                                                           Conditioning
                                                                                                       Diffusion Process                         Semantic
age from the latent, giving x̃ = D(z) = D(E(x)), where                                                                                             Map
z ∈ Rh×w×c . Importantly, the encoder downsamples the                                                      Denoising U-Net                              Text
                                                                                                                                                      Repres
image by a factor f = H/h = W/w, and we investigate                                                                                                  entations
different downsampling factors f = 2m , with m ∈ N.                                                                                                   Images
   In order to avoid arbitrarily high-variance latent spaces,
we experiment with two different kinds of regularizations.             Pixel Space
The first variant, KL-reg., imposes a slight KL-penalty to-
wards a standard normal on the learned latent, similar to a
                                                                       denoising step crossattention       switch     skip connection concat
VAE [46, 69], whereas VQ-reg. uses a vector quantization
layer [96] within the decoder. This model can be interpreted          Figure 3. We condition LDMs either via concatenation or by a
as a VQGAN [23] but with the quantization layer absorbed              more general cross-attention mechanism. See Sec. 3.3
by the decoder. Because our subsequent DM is designed
to work with the two-dimensional structure of our learned             includes the ability to build the underlying UNet primar-
latent space z = E(x), we can use relatively mild compres-            ily from 2D convolutional layers, and further focusing the
sion rates and achieve very good reconstructions. This is             objective on the perceptually most relevant bits using the
in contrast to previous works [23, 66], which relied on an            reweighted bound, which now reads
arbitrary 1D ordering of the learned space z to model its                                               h                 i
distribution autoregressively and thereby ignored much of                    LLDM := EE(x),∼N (0,1),t k − θ (zt , t)k22 . (2)
the inherent structure of z. Hence, our compression model
preserves details of x better (see Tab. 8). The full objective        The neural backbone θ (◦, t) of our model is realized as a
and training details can be found in the supplement.                  time-conditional UNet [71]. Since the forward process is
                                                                      fixed, zt can be efficiently obtained from E during training,
3.2. Latent Diffusion Models                                          and samples from p(z) can be decoded to image space with
Diffusion Models [82] are probabilistic models designed to            a single pass through D.
learn a data distribution p(x) by gradually denoising a nor-          3.3. Conditioning Mechanisms
mally distributed variable, which corresponds to learning
                                                                          Similar to other types of generative models [56, 83],
the reverse process of a fixed Markov Chain of length T .
                                                                      diffusion models are in principle capable of modeling
For image synthesis, the most successful models [15,30,72]
                                                                      conditional distributions of the form p(z|y). This can
rely on a reweighted variant of the variational lower bound
                                                                      be implemented with a conditional denoising autoencoder
on p(x), which mirrors denoising score-matching [85].
                                                                      θ (zt , t, y) and paves the way to controlling the synthesis
These models can be interpreted as an equally weighted
                                                                      process through inputs y such as text [68], semantic maps
sequence of denoising autoencoders θ (xt , t); t = 1 . . . T ,
                                                                      [33, 61] or other image-to-image translation tasks [34].
which are trained to predict a denoised variant of their input
                                                                          In the context of image synthesis, however, combining
xt , where xt is a noisy version of the input x. The corre-
                                                                      the generative power of DMs with other types of condition-
sponding objective can be simplified to (Sec. B)
                                                                      ings beyond class-labels [15] or blurred variants of the input
                                h                 i                   image [72] is so far an under-explored area of research.
         LDM = Ex,∼N (0,1),t k − θ (xt , t)k22 ,        (1)            We turn DMs into more flexible conditional image gener-
                                                                      ators by augmenting their underlying UNet backbone with
with t uniformly sampled from {1, . . . , T }.                        the cross-attention mechanism [97], which is effective for
Generative Modeling of Latent Representations With                    learning attention-based models of various input modali-
our trained perceptual compression models consisting of E             ties [35,36]. To pre-process y from various modalities (such
and D, we now have access to an efficient, low-dimensional            as language prompts) we introduce a domain specific en-
latent space in which high-frequency, imperceptible details           coder τθ that projects y to an intermediate representation
are abstracted away. Compared to the high-dimensional                 τθ (y) ∈ RM ×dτ , which is then mapped to the intermediate
pixel space, this space is more suitable for likelihood-based         layers of the UNet via a cross-attention
                                                                                                        T layer implementing
generative models, as they can now (i) focus on the impor-
                                                                      Attention(Q, K, V ) = softmax QK    √
                                                                                                            d
                                                                                                                · V , with
tant, semantic bits of the data and (ii) train in a lower di-
mensional, computationally much more efficient space.                            (i)                                (i)                        (i)
   Unlike previous work that relied on autoregressive,                Q = WQ · ϕi (zt ), K = WK · τθ (y), V = WV · τθ (y).
attention-based transformer models in a highly compressed,                                             i
discrete latent space [23, 66, 103], we can take advantage of         Here, ϕi (zt ) ∈ RN ×d denotes a (flattened) intermediate
                                                                                                                           (i)
image-specific inductive biases that our model offers. This           representation of the UNet implementing θ and WV ∈


                                                                  4
         CelebAHQ                   FFHQ                LSUN-Churches                LSUN-Beds                  ImageNet




Figure 4. Samples from LDMs trained on CelebAHQ [39], FFHQ [41], LSUN-Churches [102], LSUN-Bedrooms [102] and class-
conditional ImageNet [12], each with a resolution of 256 × 256. Best viewed when zoomed in. For more samples cf . the supplement.

     i     (i)               (i)
Rd×d , WQ ∈ Rd×dτ & WK ∈ Rd×dτ are learnable pro-                  pared in this section. Fig. 6 shows sample quality as a func-
jection matrices [36, 97]. See Fig. 3 for a visual depiction.       tion of training progress for 2M steps of class-conditional
   Based on image-conditioning pairs, we then learn the             models on the ImageNet [12] dataset. We see that, i) small
conditional LDM via                                                 downsampling factors for LDM-{1,2} result in slow train-
                               h                       i            ing progress, whereas ii) overly large values of f cause stag-
 LLDM := EE(x),y,∼N (0,1),t k−θ (zt , t, τθ (y))k22 , (3)        nating fidelity after comparably few training steps. Revis-
                                                                    iting the analysis above (Fig. 1 and 2) we attribute this to
where both τθ and θ are jointly optimized via Eq. 3. This          i) leaving most of perceptual compression to the diffusion
conditioning mechanism is flexible as τθ can be parameter-          model and ii) too strong first stage compression resulting
ized with domain-specific experts, e.g. (unmasked) trans-           in information loss and thus limiting the achievable qual-
formers [97] when y are text prompts (see Sec. 4.3.1)               ity. LDM-{4-16} strike a good balance between efficiency
                                                                    and perceptually faithful results, which manifests in a sig-
4. Experiments                                                      nificant FID [29] gap of 38 between pixel-based diffusion
   LDMs provide means to flexible and computationally               (LDM-1) and LDM-8 after 2M training steps.
tractable diffusion based image synthesis of various image              In Fig. 7, we compare models trained on CelebA-
modalities, which we empirically show in the following.             HQ [39] and ImageNet in terms sampling speed for differ-
Firstly, however, we analyze the gains of our models com-           ent numbers of denoising steps with the DDIM sampler [84]
pared to pixel-based diffusion models in both training and          and plot it against FID-scores [29]. LDM-{4-8} outper-
inference. Interestingly, we find that LDMs trained in VQ-          form models with unsuitable ratios of perceptual and con-
regularized latent spaces sometimes achieve better sample           ceptual compression. Especially compared to pixel-based
quality, even though the reconstruction capabilities of VQ-         LDM-1, they achieve much lower FID scores while simulta-
regularized first stage models slightly fall behind those of        neously significantly increasing sample throughput. Com-
their continuous counterparts, cf . Tab. 8. A visual compari-       plex datasets such as ImageNet require reduced compres-
son between the effects of first stage regularization schemes       sion rates to avoid reducing quality. In summary, LDM-4
on LDM training and their generalization abilities to resolu-       and -8 offer the best conditions for achieving high-quality
tions > 2562 can be found in Appendix D.1. In E.2 we list           synthesis results.
details on architecture, implementation, training and evalu-
ation for all results presented in this section.
                                                                    4.2. Image Generation with Latent Diffusion
4.1. On Perceptual Compression Tradeoffs
                                                                        We train unconditional models of 2562 images on
   This section analyzes the behavior of our LDMs with dif-         CelebA-HQ [39], FFHQ [41], LSUN-Churches and
ferent downsampling factors f ∈ {1, 2, 4, 8, 16, 32} (abbre-        -Bedrooms [102] and evaluate the i) sample quality and ii)
viated as LDM-f , where LDM-1 corresponds to pixel-based            their coverage of the data manifold using ii) FID [29] and
DMs). To obtain a comparable test-field, we fix the com-            ii) Precision-and-Recall [50]. Tab. 1 summarizes our re-
putational resources to a single NVIDIA A100 for all ex-            sults. On CelebA-HQ, we report a new state-of-the-art FID
periments in this section and train all models for the same         of 5.11, outperforming previous likelihood-based models as
number of steps and with the same number of parameters.             well as GANs. We also outperform LSGM [93] where a la-
   Tab. 8 shows hyperparameters and reconstruction perfor-          tent diffusion model is trained jointly together with the first
mance of the first stage models used for the LDMs com-              stage. In contrast, we train diffusion models in a fixed space


                                                                5
                                                     Text-to-Image Synthesis on LAION. 1.45B Model.
   ’A street sign that reads   ’A zombie in the    ’An image of an animal     ’An illustration of a slightly                 ’A painting of a                ’A watercolor painting of a       ’A shirt with the inscription:
     “Latent Diffusion” ’      style of Picasso’   half mouse half octopus’    conscious neural network’                 squirrel eating a burger’         chair that looks like an octopus’   “I love generative models!” ’




Figure 5. Samples for user-defined text prompts from our model for text-to-image synthesis, LDM-8 (KL), which was trained on the
LAION [78] database. Samples generated with 200 DDIM steps and η = 1.0. We use unconditional guidance [32] with s = 10.0.


                                                                                                                        CelebA-HQ 256 × 256                                              FFHQ 256 × 256
                                                                                                               Method             FID ↓    Prec. ↑    Recall ↑               Method             FID ↓        Prec. ↑   Recall ↑
                                                                                                      DC-VAE [63]                  15.8       -            -             ImageBART [21]          9.57            -         -
                                                                                                   VQGAN+T. [23] (k=400)           10.2       -            -          U-Net GAN (+aug) [77]    10.9 (7.6)        -         -
                                                                                                      PGGAN [39]                    8.0       -            -                UDM [43]             5.54            -         -
                                                                                                       LSGM [93]                   7.22       -            -              StyleGAN [41]          4.16          0.71      0.46
                                                                                                       UDM [43]                    7.16       -            -            ProjectedGAN [76]        3.08          0.65      0.46
                                                                                                     LDM-4 (ours, 500-s† )         5.11      0.72       0.49           LDM-4 (ours, 200-s)       4.98          0.73      0.50

                                                                                                                   LSUN-Churches 256 × 256                                          LSUN-Bedrooms 256 × 256
                                                                                                           Method                FID ↓     Prec. ↑     Recall ↑               Method           FID ↓        Prec. ↑    Recall ↑
                                                                                                         DDPM [30]                7.89         -          -              ImageBART [21]         5.51           -          -
                                                                                                      ImageBART [21]              7.32         -          -                DDPM [30]            4.9            -          -
Figure 6. Analyzing the training of class-conditional LDMs with                                         PGGAN [39]                6.42         -          -                 UDM [43]            4.57           -          -
                                                                                                       StyleGAN [41]              4.21         -          -               StyleGAN [41]         2.35         0.59       0.48
different downsampling factors f over 2M train steps on the Im-                                        StyleGAN2 [42]             3.86         -          -                 ADM [15]            1.90         0.66       0.51
                                                                                                     ProjectedGAN [76]            1.59       0.61       0.44            ProjectedGAN [76]       1.52         0.61       0.34
ageNet dataset. Pixel-based LDM-1 requires substantially larger
                                                                                                    LDM-8∗ (ours, 200-s)          4.02       0.64       0.52            LDM-4 (ours, 200-s)     2.95         0.66       0.48
train times compared to models with larger downsampling factors
(LDM-{4-16}). Too much perceptual compression as in LDM-32                                        Table 1. Evaluation metrics for unconditional image synthesis.
limits the overall sample quality. All models are trained on a sin-                               CelebA-HQ results reproduced from [43, 63, 100], FFHQ from
gle NVIDIA A100 with the same computational budget. Results                                       [42, 43]. † : N -s refers to N sampling steps with the DDIM [84]
obtained with 100 DDIM steps [84] and κ = 0.                                                      sampler. ∗ : trained in KL-regularized latent space. Additional re-
                                                                                                  sults can be found in the supplementary.

                                                                                                                                             Text-Conditional Image Synthesis
                                                                                                    Method                           FID ↓           IS↑          Nparams
                                                                                                    CogView† [17]                    27.10           18.20            4B            self-ranking, rejection rate 0.017
                                                                                                    LAFITE† [109]                    26.94           26.02           75M
                                                                                                    GLIDE∗ [59]                      12.24             -              6B           277 DDIM steps, c.f.g. [32] s = 3
                                                                                                    Make-A-Scene∗ [26]               11.84             -              4B            c.f.g for AR models [98] s = 5
                                                                                                    LDM-KL-8                         23.31        20.03±0.33        1.45B                 250 DDIM steps
                                                                                                    LDM-KL-8-G∗                      12.63        30.29±0.42        1.45B         250 DDIM steps, c.f.g. [32] s = 1.5
Figure 7. Comparing LDMs with varying compression on the
CelebA-HQ (left) and ImageNet (right) datasets. Different mark-                                   Table 2. Evaluation of text-conditional image synthesis on the
ers indicate {10, 20, 50, 100, 200} sampling steps using DDIM,                                    256 × 256-sized MS-COCO [51] dataset: with 250 DDIM [84]
from right to left along each line. The dashed line shows the FID                                 steps our model is on par with the most recent diffusion [59] and
scores for 200 steps, indicating the strong performance of LDM-                                   autoregressive [26] methods despite using significantly less pa-
{4-8}. FID scores assessed on 5000 samples. All models were                                       rameters. † /∗ :Numbers from [109]/ [26]
trained for 500k (CelebA) / 2M (ImageNet) steps on an A100.
and avoid the difficulty of weighing reconstruction quality
against learning the prior over the latent space, see Fig. 1-2.                                   Moreover, LDMs consistently improve upon GAN-based
   We outperform prior diffusion based approaches on all                                          methods in Precision and Recall, thus confirming the ad-
but the LSUN-Bedrooms dataset, where our score is close                                           vantages of their mode-covering likelihood-based training
to ADM [15], despite utilizing half its parameters and re-                                        objective over adversarial approaches. In Fig. 4 we also
quiring 4-times less train resources (see Appendix E.3.5).                                        show qualitative results on each dataset.


                                                                                          6
                                                                      Method            FID↓       IS↑        Precision↑   Recall↑   Nparams
                                                                      BigGan-deep [3]   6.95    203.6±2.6       0.87        0.28      340M                 -
                                                                      ADM [15]          10.94    100.98         0.69        0.63      554M           250 DDIM steps
                                                                      ADM-G [15]        4.59      186.7         0.82        0.52      608M           250 DDIM steps
                                                                      LDM-4 (ours)      10.56   103.49±1.24     0.71        0.62      400M           250 DDIM steps
                                                                      LDM-4-G (ours)    3.60    247.67±5.59     0.87        0.48      400M     250 steps, c.f.g [32], s = 1.5



                                                                     Table 3. Comparison of a class-conditional ImageNet LDM with
                                                                     recent state-of-the-art methods for class-conditional image gener-
                                                                     ation on ImageNet [12]. A more detailed comparison with addi-
                                                                     tional baselines can be found in D.4, Tab. 10 and F. c.f.g. denotes
                                                                     classifier-free guidance with a scale s as proposed in [32].


                                                                     purpose image-to-image translation models. We use this
Figure 8. Layout-to-image synthesis with an LDM on COCO [4],         to train models for semantic synthesis, super-resolution
see Sec. 4.3.1. Quantitative evaluation in the supplement D.3.       (Sec. 4.4) and inpainting (Sec. 4.5). For semantic synthe-
                                                                     sis, we use images of landscapes paired with semantic maps
4.3. Conditional Latent Diffusion                                    [23, 61] and concatenate downsampled versions of the se-
                                                                     mantic maps with the latent image representation of a f = 4
4.3.1 Transformer Encoders for LDMs                                  model (VQ-reg., see Tab. 8). We train on an input resolution
By introducing cross-attention based conditioning into               of 2562 (crops from 3842 ) but find that our model general-
LDMs we open them up for various conditioning modali-                izes to larger resolutions and can generate images up to the
ties previously unexplored for diffusion models. For text-           megapixel regime when evaluated in a convolutional man-
to-image image modeling, we train a 1.45B parameter                  ner (see Fig. 9). We exploit this behavior to also apply the
KL-regularized LDM conditioned on language prompts on                super-resolution models in Sec. 4.4 and the inpainting mod-
LAION-400M [78]. We employ the BERT-tokenizer [14]                   els in Sec. 4.5 to generate large images between 5122 and
and implement τθ as a transformer [97] to infer a latent             10242 . For this application, the signal-to-noise ratio (in-
code which is mapped into the UNet via (multi-head) cross-           duced by the scale of the latent space) significantly affects
attention (Sec. 3.3). This combination of domain specific            the results. In Sec. D.1 we illustrate this when learning an
experts for learning a language representation and visual            LDM on (i) the latent space as provided by a f = 4 model
synthesis results in a powerful model, which generalizes             (KL-reg., see Tab. 8), and (ii) a rescaled version, scaled by
well to complex, user-defined text prompts, cf . Fig. 8 and 5.       the component-wise standard deviation.
For quantitative analysis, we follow prior work and evaluate             The latter, in combination with classifier-free guid-
text-to-image generation on the MS-COCO [51] validation              ance [32], also enables the direct synthesis of > 2562 im-
set, where our model improves upon powerful AR [17, 66]              ages for the text-conditional LDM-KL-8-G as in Fig. 13.
and GAN-based [109] methods, cf . Tab. 2. We note that ap-
plying classifier-free diffusion guidance [32] greatly boosts
sample quality, such that the guided LDM-KL-8-G is on par
with the recent state-of-the-art AR [26] and diffusion mod-
els [59] for text-to-image synthesis, while substantially re-
ducing parameter count. To further analyze the flexibility of
the cross-attention based conditioning mechanism we also
train models to synthesize images based on semantic lay-
outs on OpenImages [49], and finetune on COCO [4], see
Fig. 8. See Sec. D.3 for the quantitative evaluation and im-
plementation details.
    Lastly, following prior work [3, 15, 21, 23], we evalu-
ate our best-performing class-conditional ImageNet mod-
els with f ∈ {4, 8} from Sec. 4.1 in Tab. 3, Fig. 4 and              Figure 9. A LDM trained on 2562 resolution can generalize to
Sec. D.4. Here we outperform the state of the art diffu-             larger resolution (here: 512×1024) for spatially conditioned tasks
sion model ADM [15] while significantly reducing compu-              such as semantic synthesis of landscape images. See Sec. 4.3.2.
tational requirements and parameter count, cf . Tab 18.              4.4. Super-Resolution with Latent Diffusion
4.3.2 Convolutional Sampling Beyond 2562                                LDMs can be efficiently trained for super-resolution by
By concatenating spatially aligned conditioning informa-             diretly conditioning on low-resolution images via concate-
tion to the input of θ , LDMs can serve as efficient general-       nation (cf . Sec. 3.3). In a first experiment, we follow SR3


                                                                 7
                                                                                                                                                                                   samples ∗
                                                                                    Method                                FID ↓      IS ↑    PSNR ↑     SSIM ↑      Nparams    [
                                                                                                                                                                                      s
                                                                                                                                                                                          ]( )


        bicubic                   LDM-SR                   SR3                      Image Regression [72]                 15.2       121.1    27.9       0.801       625M            N/A
                                                                                    SR3 [72]                               5.2       180.1    26.4       0.762       625M            N/A
                                                                                    LDM-4 (ours, 100 steps)             2.8† /4.8‡   166.3   24.4±3.8   0.69±0.14    169M            4.62
                                                                                    emphLDM-4 (ours, big, 100 steps)    2.4† /4.3‡   174.9   24.7±4.1   0.71±0.15    552M             4.5
                                                                                    LDM-4 (ours, 50 steps, guiding)     4.4† /6.4‡   153.7   25.8±3.7   0.74±0.12    184M            0.38

                                                                                   Table 5. ×4 upscaling results on ImageNet-Val. (2562 ); † : FID
                                                                                   features computed on validation split, ‡ : FID features computed
                                                                                   on train split; ∗ : Assessed on a NVIDIA A100

                                                                                                               train throughput      sampling throughput†         train+val    FID@2k
                                                                                    Model (reg.-type)            samples/sec.        @256           @512         hours/epoch   epoch 6
                                                                                    LDM-1 (no first stage)             0.11           0.26              0.07        20.66          24.74
                                                                                    LDM-4 (KL, w/ attn)                0.32           0.97              0.34         7.66          15.21
                                                                                    LDM-4 (VQ, w/ attn)                0.33           0.97              0.34         7.04          14.99
                                                                                    LDM-4 (VQ, w/o attn)               0.35           0.99              0.36         6.66          15.95

                                                                                   Table 6. Assessing inpainting efficiency. † : Deviations from Fig. 7
                                                                                   due to varying GPU settings/batch sizes cf . the supplement.
Figure 10. ImageNet 64→256 super-resolution on ImageNet-Val.                       4.5. Inpainting with Latent Diffusion
LDM-SR has advantages at rendering realistic textures but SR3
can synthesize more coherent fine structures. See appendix for                         Inpainting is the task of filling masked regions of an im-
additional samples and cropouts. SR3 results from [72].                            age with new content either because parts of the image are
                                                                                   are corrupted or to replace existing but undesired content
                                                                                   within the image. We evaluate how our general approach
[72] and fix the image degradation to a bicubic interpola-                         for conditional image generation compares to more special-
tion with 4×-downsampling and train on ImageNet follow-                            ized, state-of-the-art approaches for this task. Our evalua-
ing SR3’s data processing pipeline. We use the f = 4 au-                           tion follows the protocol of LaMa [88], a recent inpainting
toencoding model pretrained on OpenImages (VQ-reg., cf .                           model that introduces a specialized architecture relying on
Tab. 8) and concatenate the low-resolution conditioning y                          Fast Fourier Convolutions [8]. The exact training & evalua-
and the inputs to the UNet, i.e. τθ is the identity. Our quali-                    tion protocol on Places [108] is described in Sec. E.2.2.
tative and quantitative results (see Fig. 10 and Tab. 5) show                          We first analyze the effect of different design choices for
competitive performance and LDM-SR outperforms SR3                                 the first stage. In particular, we compare the inpainting ef-
in FID while SR3 has a better IS. A simple image regres-                           ficiency of LDM-1 (i.e. a pixel-based conditional DM) with
sion model achieves the highest PSNR and SSIM scores;                              LDM-4, for both KL and VQ regularizations, as well as VQ-
however these metrics do not align well with human per-                            LDM-4 without any attention in the first stage (see Tab. 8),
ception [106] and favor blurriness over imperfectly aligned                        where the latter reduces GPU memory for decoding at high
high frequency details [72]. Further, we conduct a user                            resolutions. For comparability, we fix the number of param-
study comparing the pixel-baseline with LDM-SR. We fol-                            eters for all models. Tab. 6 reports the training and sampling
low SR3 [72] where human subjects were shown a low-res                             throughput at resolution 2562 and 5122 , the total training
image in between two high-res images and asked for pref-                           time in hours per epoch and the FID score on the validation
erence. The results in Tab. 4 affirm the good performance                          split after six epochs. Overall, we observe a speed-up of at
of LDM-SR. PSNR and SSIM can be pushed by using a                                  least 2.7× between pixel- and latent-based diffusion models
post-hoc guiding mechanism [15] and we implement this                              while improving FID scores by a factor of at least 1.6×.
image-based guider via a perceptual loss, see Sec. D.6.                                The comparison with other inpainting approaches in
                                                                                   Tab. 7 shows that our model with attention improves the
                                                                                   overall image quality as measured by FID over that of [88].
                                  SR on ImageNet        Inpainting on Places       LPIPS between the unmasked images and our samples is
 User Study                   Pixel-DM (f 1)   LDM-4   LAMA [88]      LDM-4        slightly higher than that of [88]. We attribute this to [88]
 Task 1: Preference vs GT ↑       16.0%        30.4%     13.6%        21.0%        only producing a single result which tends to recover more
 Task 2: Preference Score ↑       29.4%        70.6%     31.9%        68.1%
                                                                                   of an average image compared to the diverse results pro-
Table 4. Task 1: Subjects were shown ground truth and generated                    duced by our LDM cf . Fig. 21. Additionally in a user study
image and asked for preference. Task 2: Subjects had to decide                     (Tab. 4) human subjects favor our results over those of [88].
between two generated images. More details in E.3.6
                                                                                       Based on these initial results, we also trained a larger dif-
                                                                                   fusion model (big in Tab. 7) in the latent space of the VQ-
Since the bicubic degradation process does not generalize                          regularized first stage without attention. Following [15],
well to images which do not follow this pre-processing, we                         the UNet of this diffusion model uses attention layers on
also train a generic model, LDM-BSR, by using more di-                             three levels of its feature hierarchy, the BigGAN [3] residual
verse degradation. The results are shown in Sec. D.6.1.                            block for up- and downsampling and has 387M parameters


                                                                               8
              input                           result                                                  40-50% masked            All samples
                                                                         Method                      FID ↓     LPIPS ↓      FID ↓     LPIPS ↓
                                                                         LDM-4 (ours, big, w/ ft)     9.39   0.246± 0.042    1.50   0.137± 0.080
                                                                         LDM-4 (ours, big, w/o ft)   12.89   0.257± 0.047    2.40   0.142± 0.085
                                                                         LDM-4 (ours, w/ attn)       11.87   0.257± 0.042    2.15   0.144± 0.084
                                                                         LDM-4 (ours, w/o attn)      12.60   0.259± 0.041    2.37   0.145± 0.084
                                                                         LaMa [88]†                  12.31   0.243± 0.038    2.23   0.134± 0.080
                                                                         LaMa [88]                   12.0     0.24           2.21    0.14
                                                                         CoModGAN [107]              10.4     0.26           1.82    0.15
                                                                         RegionWise [52]             21.3     0.27           4.75    0.15
                                                                         DeepFill v2 [104]           22.1     0.28           5.20    0.16
                                                                         EdgeConnect [58]            30.5     0.28           8.37    0.16

                                                                        Table 7. Comparison of inpainting performance on 30k crops of
                                                                        size 512 × 512 from test images of Places [108]. The column 40-
                                                                        50% reports metrics computed over hard examples where 40-50%
                                                                        of the image region have to be inpainted. † recomputed on our test
                                                                        set, since the original test set used in [88] was not available.

                                                                        enable various creative applications, and in particular ap-
                                                                        proaches like ours that reduce the cost of training and in-
                                                                        ference have the potential to facilitate access to this tech-
                                                                        nology and democratize its exploration. On the other hand,
                                                                        it also means that it becomes easier to create and dissemi-
                                                                        nate manipulated data or spread misinformation and spam.
                                                                        In particular, the deliberate manipulation of images (“deep
                                                                        fakes”) is a common problem in this context, and women in
                                                                        particular are disproportionately affected by it [13, 24].
                                                                            Generative models can also reveal their training data
                                                                        [5, 90], which is of great concern when the data contain
                                                                        sensitive or personal information and were collected with-
                                                                        out explicit consent. However, the extent to which this also
                                                                        applies to DMs of images is not yet fully understood.
Figure 11. Qualitative results on object removal with our big, w/           Finally, deep learning modules tend to reproduce or ex-
ft inpainting model. For more results, see Fig. 22.                     acerbate biases that are already present in the data [22, 38,
instead of 215M. After training, we noticed a discrepancy               91]. While diffusion models achieve better coverage of the
in the quality of samples produced at resolutions 2562 and              data distribution than e.g. GAN-based approaches, the ex-
5122 , which we hypothesize to be caused by the additional              tent to which our two-stage approach that combines adver-
attention modules. However, fine-tuning the model for half              sarial training and a likelihood-based objective misrepre-
an epoch at resolution 5122 allows the model to adjust to               sents the data remains an important research question.
the new feature statistics and sets a new state of the art FID              For a more general, detailed discussion of the ethical
on image inpainting (big, w/o attn, w/ ft in Tab. 7, Fig. 11.).         considerations of deep generative models, see e.g. [13].
                                                                        6. Conclusion
5. Limitations & Societal Impact
                                                                            We have presented latent diffusion models, a simple and
Limitations While LDMs significantly reduce computa-                    efficient way to significantly improve both the training and
tional requirements compared to pixel-based approaches,                 sampling efficiency of denoising diffusion models with-
their sequential sampling process is still slower than that             out degrading their quality. Based on this and our cross-
of GANs. Moreover, the use of LDMs can be question-                     attention conditioning mechanism, our experiments could
able when high precision is required: although the loss of              demonstrate favorable results compared to state-of-the-art
image quality is very small in our f = 4 autoencoding mod-              methods across a wide range of conditional image synthesis
els (see Fig. 1), their reconstruction capability can become            tasks without task-specific architectures.
a bottleneck for tasks that require fine-grained accuracy in
pixel space. We assume that our superresolution models
(Sec. 4.4) are already somewhat limited in this respect.                    This work has been supported by the German Federal Ministry for
                                                                        Economic Affairs and Energy within the project ’KI-Absicherung - Safe
Societal Impact Generative models for media like im-                    AI for automated driving’ and by the German Research Foundation (DFG)
agery are a double-edged sword: On the one hand, they                   project 421703927.

                                                                    9
References                                                              [16] Sander Dieleman. Musings on typicality, 2020. 1, 3
                                                                        [17] Ming Ding, Zhuoyi Yang, Wenyi Hong, Wendi Zheng,
 [1] Eirikur Agustsson and Radu Timofte. NTIRE 2017 chal-
                                                                             Chang Zhou, Da Yin, Junyang Lin, Xu Zou, Zhou Shao,
     lenge on single image super-resolution: Dataset and study.
                                                                             Hongxia Yang, and Jie Tang. Cogview: Mastering text-to-
     In 2017 IEEE Conference on Computer Vision and Pattern
                                                                             image generation via transformers. CoRR, abs/2105.13290,
     Recognition Workshops, CVPR Workshops 2017, Honolulu,
                                                                             2021. 6, 7
     HI, USA, July 21-26, 2017, pages 1122–1131. IEEE Com-
                                                                        [18] Laurent Dinh, David Krueger, and Yoshua Bengio. Nice:
     puter Society, 2017. 1
                                                                             Non-linear independent components estimation, 2015. 3
 [2] Martin Arjovsky, Soumith Chintala, and Léon Bottou.
                                                                        [19] Laurent Dinh, Jascha Sohl-Dickstein, and Samy Ben-
     Wasserstein gan, 2017. 3
                                                                             gio. Density estimation using real NVP. In 5th Inter-
 [3] Andrew Brock, Jeff Donahue, and Karen Simonyan. Large
                                                                             national Conference on Learning Representations, ICLR
     scale GAN training for high fidelity natural image synthe-
                                                                             2017, Toulon, France, April 24-26, 2017, Conference Track
     sis. In Int. Conf. Learn. Represent., 2019. 1, 2, 7, 8, 22,
                                                                             Proceedings. OpenReview.net, 2017. 1, 3
     28
                                                                        [20] Alexey Dosovitskiy and Thomas Brox. Generating images
 [4] Holger Caesar, Jasper R. R. Uijlings, and Vittorio Ferrari.
                                                                             with perceptual similarity metrics based on deep networks.
     Coco-stuff: Thing and stuff classes in context. In 2018
                                                                             In Daniel D. Lee, Masashi Sugiyama, Ulrike von Luxburg,
     IEEE Conference on Computer Vision and Pattern Recog-
                                                                             Isabelle Guyon, and Roman Garnett, editors, Adv. Neural
     nition, CVPR 2018, Salt Lake City, UT, USA, June 18-
                                                                             Inform. Process. Syst., pages 658–666, 2016. 3
     22, 2018, pages 1209–1218. Computer Vision Foundation /
     IEEE Computer Society, 2018. 7, 20, 22                             [21] Patrick Esser, Robin Rombach, Andreas Blattmann, and
 [5] Nicholas Carlini, Florian Tramer, Eric Wallace, Matthew                 Björn Ommer. Imagebart: Bidirectional context with multi-
     Jagielski, Ariel Herbert-Voss, Katherine Lee, Adam                      nomial diffusion for autoregressive image synthesis. CoRR,
     Roberts, Tom Brown, Dawn Song, Ulfar Erlingsson, et al.                 abs/2108.08827, 2021. 6, 7, 22
     Extracting training data from large language models. In            [22] Patrick Esser, Robin Rombach, and Björn Ommer. A
     30th USENIX Security Symposium (USENIX Security 21),                    note on data biases in generative models. arXiv preprint
     pages 2633–2650, 2021. 9                                                arXiv:2012.02516, 2020. 9
 [6] Mark Chen, Alec Radford, Rewon Child, Jeffrey Wu, Hee-             [23] Patrick Esser, Robin Rombach, and Björn Ommer. Taming
     woo Jun, David Luan, and Ilya Sutskever. Generative pre-                transformers for high-resolution image synthesis. CoRR,
     training from pixels. In ICML, volume 119 of Proceedings                abs/2012.09841, 2020. 2, 3, 4, 6, 7, 21, 22, 29, 34, 36
     of Machine Learning Research, pages 1691–1703. PMLR,               [24] Mary Anne Franks and Ari Ezra Waldman. Sex, lies, and
     2020. 3                                                                 videotape: Deep fakes and free speech delusions. Md. L.
 [7] Nanxin Chen, Yu Zhang, Heiga Zen, Ron J. Weiss, Mo-                     Rev., 78:892, 2018. 9
     hammad Norouzi, and William Chan. Wavegrad: Estimat-               [25] Kevin Frans, Lisa B. Soros, and Olaf Witkowski. Clipdraw:
     ing gradients for waveform generation. In ICLR. OpenRe-                 Exploring text-to-drawing synthesis through language-
     view.net, 2021. 1                                                       image encoders. ArXiv, abs/2106.14843, 2021. 3
 [8] Lu Chi, Borui Jiang, and Yadong Mu. Fast fourier convolu-          [26] Oran Gafni, Adam Polyak, Oron Ashual, Shelly Sheynin,
     tion. In NeurIPS, 2020. 8                                               Devi Parikh, and Yaniv Taigman. Make-a-scene: Scene-
 [9] Rewon Child. Very deep vaes generalize autoregressive                   based text-to-image generation with human priors. CoRR,
     models and can outperform them on images. CoRR,                         abs/2203.13131, 2022. 6, 7, 16
     abs/2011.10650, 2020. 3                                            [27] Ian J. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing
[10] Rewon Child, Scott Gray, Alec Radford, and Ilya Sutskever.              Xu, David Warde-Farley, Sherjil Ozair, Aaron C. Courville,
     Generating long sequences with sparse transformers.                     and Yoshua Bengio. Generative adversarial networks.
     CoRR, abs/1904.10509, 2019. 3                                           CoRR, 2014. 1, 2
[11] Bin Dai and David P. Wipf. Diagnosing and enhancing VAE            [28] Ishaan Gulrajani, Faruk Ahmed, Martin Arjovsky, Vincent
     models. In ICLR (Poster). OpenReview.net, 2019. 2, 3                    Dumoulin, and Aaron Courville. Improved training of
[12] Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li,                  wasserstein gans, 2017. 3
     and Fei-Fei Li. Imagenet: A large-scale hierarchical im-           [29] Martin Heusel, Hubert Ramsauer, Thomas Unterthiner,
     age database. In CVPR, pages 248–255. IEEE Computer                     Bernhard Nessler, and Sepp Hochreiter. Gans trained by
     Society, 2009. 1, 5, 7, 22                                              a two time-scale update rule converge to a local nash equi-
[13] Emily Denton. Ethical considerations of generative ai. AI               librium. In Adv. Neural Inform. Process. Syst., pages 6626–
     for Content Creation Workshop, CVPR, 2021. 9                            6637, 2017. 1, 5, 26
[14] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and                      [30] Jonathan Ho, Ajay Jain, and Pieter Abbeel. Denoising dif-
     Kristina Toutanova. BERT: pre-training of deep bidirec-                 fusion probabilistic models. In NeurIPS, 2020. 1, 2, 3, 4,
     tional transformers for language understanding. CoRR,                   6, 17
     abs/1810.04805, 2018. 7                                            [31] Jonathan Ho, Chitwan Saharia, William Chan, David J.
[15] Prafulla Dhariwal and Alex Nichol. Diffusion models beat                Fleet, Mohammad Norouzi, and Tim Salimans. Cascaded
     gans on image synthesis. CoRR, abs/2105.05233, 2021. 1,                 diffusion models for high fidelity image generation. CoRR,
     2, 3, 4, 6, 7, 8, 18, 22, 25, 26, 28                                    abs/2106.15282, 2021. 1, 3, 22


                                                                   10
[32] Jonathan Ho and Tim Salimans. Classifier-free diffusion             [45] Diederik P. Kingma, Tim Salimans, Ben Poole, and
     guidance. In NeurIPS 2021 Workshop on Deep Generative                    Jonathan Ho.       Variational diffusion models.      CoRR,
     Models and Downstream Applications, 2021. 6, 7, 16, 22,                  abs/2107.00630, 2021. 1, 3, 16
     28, 37, 38                                                          [46] Diederik P. Kingma and Max Welling. Auto-Encoding Vari-
[33] Phillip Isola, Jun-Yan Zhu, Tinghui Zhou, and Alexei A.                  ational Bayes. In 2nd International Conference on Learn-
     Efros. Image-to-image translation with conditional adver-                ing Representations, ICLR, 2014. 1, 3, 4, 29
     sarial networks. In CVPR, pages 5967–5976. IEEE Com-                [47] Zhifeng Kong and Wei Ping. On fast sampling of diffusion
     puter Society, 2017. 3, 4                                                probabilistic models. CoRR, abs/2106.00132, 2021. 3
[34] Phillip Isola, Jun-Yan Zhu, Tinghui Zhou, and Alexei A.             [48] Zhifeng Kong, Wei Ping, Jiaji Huang, Kexin Zhao, and
     Efros. Image-to-image translation with conditional adver-                Bryan Catanzaro. Diffwave: A versatile diffusion model
     sarial networks. 2017 IEEE Conference on Computer Vi-                    for audio synthesis. In ICLR. OpenReview.net, 2021. 1
     sion and Pattern Recognition (CVPR), pages 5967–5976,               [49] Alina Kuznetsova, Hassan Rom, Neil Alldrin, Jasper R. R.
     2017. 4                                                                  Uijlings, Ivan Krasin, Jordi Pont-Tuset, Shahab Kamali,
[35] Andrew Jaegle, Sebastian Borgeaud, Jean-Baptiste                         Stefan Popov, Matteo Malloci, Tom Duerig, and Vittorio
     Alayrac, Carl Doersch, Catalin Ionescu, David Ding,                      Ferrari. The open images dataset V4: unified image classi-
     Skanda Koppula, Daniel Zoran, Andrew Brock, Evan                         fication, object detection, and visual relationship detection
     Shelhamer, Olivier J. Hénaff, Matthew M. Botvinick,                     at scale. CoRR, abs/1811.00982, 2018. 7, 20, 22
     Andrew Zisserman, Oriol Vinyals, and João Carreira.                [50] Tuomas Kynkäänniemi, Tero Karras, Samuli Laine, Jaakko
     Perceiver IO: A general architecture for structured inputs               Lehtinen, and Timo Aila. Improved precision and re-
     &outputs. CoRR, abs/2107.14795, 2021. 4                                  call metric for assessing generative models.          CoRR,
[36] Andrew Jaegle, Felix Gimeno, Andy Brock, Oriol Vinyals,                  abs/1904.06991, 2019. 5, 26
     Andrew Zisserman, and João Carreira. Perceiver: General
                                                                         [51] Tsung-Yi Lin, Michael Maire, Serge J. Belongie,
     perception with iterative attention. In Marina Meila and
                                                                              Lubomir D. Bourdev, Ross B. Girshick, James Hays, Pietro
     Tong Zhang, editors, Proceedings of the 38th International
                                                                              Perona, Deva Ramanan, Piotr Dollár, and C. Lawrence Zit-
     Conference on Machine Learning, ICML 2021, 18-24 July
                                                                              nick. Microsoft COCO: common objects in context. CoRR,
     2021, Virtual Event, volume 139 of Proceedings of Machine
                                                                              abs/1405.0312, 2014. 6, 7, 27
     Learning Research, pages 4651–4664. PMLR, 2021. 4, 5
                                                                         [52] Yuqing Ma, Xianglong Liu, Shihao Bai, Le-Yi Wang, Ais-
[37] Manuel Jahn, Robin Rombach, and Björn Ommer. High-
                                                                              han Liu, Dacheng Tao, and Edwin Hancock. Region-wise
     resolution complex scene synthesis with transformers.
                                                                              generative adversarial imageinpainting for large missing ar-
     CoRR, abs/2105.06458, 2021. 20, 22, 27
                                                                              eas. ArXiv, abs/1909.12507, 2019. 9
[38] Niharika Jain, Alberto Olmo, Sailik Sengupta, Lydia
                                                                         [53] Chenlin Meng, Yang Song, Jiaming Song, Jiajun Wu, Jun-
     Manikonda, and Subbarao Kambhampati. Imperfect ima-
                                                                              Yan Zhu, and Stefano Ermon. Sdedit: Image synthesis
     ganation: Implications of gans exacerbating biases on fa-
                                                                              and editing with stochastic differential equations. CoRR,
     cial data augmentation and snapchat selfie lenses. arXiv
                                                                              abs/2108.01073, 2021. 1
     preprint arXiv:2001.09528, 2020. 9
[39] Tero Karras, Timo Aila, Samuli Laine, and Jaakko Lehti-             [54] Lars M. Mescheder. On the convergence properties of GAN
     nen. Progressive growing of gans for improved quality, sta-              training. CoRR, abs/1801.04406, 2018. 3
     bility, and variation. CoRR, abs/1710.10196, 2017. 5, 6             [55] Luke Metz, Ben Poole, David Pfau, and Jascha Sohl-
[40] Tero Karras, Samuli Laine, and Timo Aila. A style-based                  Dickstein. Unrolled generative adversarial networks. In
     generator architecture for generative adversarial networks.              5th International Conference on Learning Representations,
     In IEEE Conf. Comput. Vis. Pattern Recog., pages 4401–                   ICLR 2017, Toulon, France, April 24-26, 2017, Conference
     4410, 2019. 1                                                            Track Proceedings. OpenReview.net, 2017. 3
[41] T. Karras, S. Laine, and T. Aila. A style-based gener-              [56] Mehdi Mirza and Simon Osindero. Conditional generative
     ator architecture for generative adversarial networks. In                adversarial nets. CoRR, abs/1411.1784, 2014. 4
     2019 IEEE/CVF Conference on Computer Vision and Pat-                [57] Gautam Mittal, Jesse H. Engel, Curtis Hawthorne, and Ian
     tern Recognition (CVPR), 2019. 5, 6                                      Simon. Symbolic music generation with diffusion models.
[42] Tero Karras, Samuli Laine, Miika Aittala, Janne Hellsten,                CoRR, abs/2103.16091, 2021. 1
     Jaakko Lehtinen, and Timo Aila. Analyzing and improv-               [58] Kamyar Nazeri, Eric Ng, Tony Joseph, Faisal Z. Qureshi,
     ing the image quality of stylegan. CoRR, abs/1912.04958,                 and Mehran Ebrahimi. Edgeconnect: Generative im-
     2019. 2, 6, 28                                                           age inpainting with adversarial edge learning. ArXiv,
[43] Dongjun Kim, Seungjae Shin, Kyungwoo Song, Wanmo                         abs/1901.00212, 2019. 9
     Kang, and Il-Chul Moon. Score matching model for un-                [59] Alex Nichol, Prafulla Dhariwal, Aditya Ramesh, Pranav
     bounded data score. CoRR, abs/2106.05527, 2021. 6                        Shyam, Pamela Mishkin, Bob McGrew, Ilya Sutskever, and
[44] Durk P Kingma and Prafulla Dhariwal. Glow: Generative                    Mark Chen. GLIDE: towards photorealistic image genera-
     flow with invertible 1x1 convolutions. In S. Bengio, H. Wal-             tion and editing with text-guided diffusion models. CoRR,
     lach, H. Larochelle, K. Grauman, N. Cesa-Bianchi, and R.                 abs/2112.10741, 2021. 6, 7, 16
     Garnett, editors, Advances in Neural Information Process-           [60] Anton Obukhov, Maximilian Seitzer, Po-Wei Wu, Se-
     ing Systems, 2018. 3                                                     men Zhydenko, Jonathan Kyl, and Elvis Yu-Jing Lin.


                                                                    11
     High-fidelity performance metrics for generative models                    immediate- speedups- with- a100- tf32, 2020.
     in pytorch, 2020. Version: 0.3.0, DOI: 10.5281/zen-                        28
     odo.4957738. 26, 27                                                   [75] Robin San-Roman, Eliya Nachmani, and Lior Wolf.
[61] Taesung Park, Ming-Yu Liu, Ting-Chun Wang, and Jun-                        Noise estimation for generative diffusion models. CoRR,
     Yan Zhu. Semantic image synthesis with spatially-adaptive                  abs/2104.02600, 2021. 3
     normalization. In Proceedings of the IEEE Conference on               [76] Axel Sauer, Kashyap Chitta, Jens Müller, and An-
     Computer Vision and Pattern Recognition, 2019. 4, 7                        dreas Geiger. Projected gans converge faster. CoRR,
[62] Taesung Park, Ming-Yu Liu, Ting-Chun Wang, and Jun-                        abs/2111.01007, 2021. 6
     Yan Zhu. Semantic image synthesis with spatially-adaptive             [77] Edgar Schönfeld, Bernt Schiele, and Anna Khoreva. A u-
     normalization. In Proceedings of the IEEE/CVF Confer-                      net based discriminator for generative adversarial networks.
     ence on Computer Vision and Pattern Recognition (CVPR),                    In 2020 IEEE/CVF Conference on Computer Vision and
     June 2019. 22                                                              Pattern Recognition, CVPR 2020, Seattle, WA, USA, June
[63] Gaurav Parmar, Dacheng Li, Kwonjoon Lee, and Zhuowen                       13-19, 2020, pages 8204–8213. Computer Vision Founda-
     Tu. Dual contradistinctive generative autoencoder. In IEEE                 tion / IEEE, 2020. 6
     Conference on Computer Vision and Pattern Recognition,
                                                                           [78] Christoph Schuhmann, Richard Vencu, Romain Beaumont,
     CVPR 2021, virtual, June 19-25, 2021, pages 823–832.
                                                                                Robert Kaczmarczyk, Clayton Mullis, Aarush Katta, Theo
     Computer Vision Foundation / IEEE, 2021. 6
                                                                                Coombes, Jenia Jitsev, and Aran Komatsuzaki. Laion-
[64] Gaurav Parmar, Richard Zhang, and Jun-Yan Zhu. On                          400m: Open dataset of clip-filtered 400 million image-text
     buggy resizing libraries and surprising subtleties in fid cal-             pairs, 2021. 6, 7
     culation. arXiv preprint arXiv:2104.11222, 2021. 26
                                                                           [79] Karen Simonyan and Andrew Zisserman. Very deep con-
[65] David A. Patterson, Joseph Gonzalez, Quoc V. Le, Chen
                                                                                volutional networks for large-scale image recognition. In
     Liang, Lluis-Miquel Munguia, Daniel Rothchild, David R.
                                                                                Yoshua Bengio and Yann LeCun, editors, Int. Conf. Learn.
     So, Maud Texier, and Jeff Dean. Carbon emissions and
                                                                                Represent., 2015. 29, 43, 44, 45
     large neural network training. CoRR, abs/2104.10350,
     2021. 2                                                               [80] Abhishek Sinha, Jiaming Song, Chenlin Meng, and Stefano
[66] Aditya Ramesh, Mikhail Pavlov, Gabriel Goh, Scott                          Ermon. D2C: diffusion-denoising models for few-shot con-
     Gray, Chelsea Voss, Alec Radford, Mark Chen, and Ilya                      ditional generation. CoRR, abs/2106.06819, 2021. 3
     Sutskever. Zero-shot text-to-image generation. CoRR,                  [81] Charlie Snell. Alien Dreams: An Emerging Art Scene.
     abs/2102.12092, 2021. 1, 2, 3, 4, 7, 21, 27                                https : / / ml . berkeley . edu / blog / posts /
[67] Ali Razavi, Aäron van den Oord, and Oriol Vinyals. Gen-                   clip-art/, 2021. [Online; accessed November-2021].
     erating diverse high-fidelity images with VQ-VAE-2. In                     2
     NeurIPS, pages 14837–14847, 2019. 1, 2, 3, 22                         [82] Jascha Sohl-Dickstein, Eric A. Weiss, Niru Mah-
[68] Scott E. Reed, Zeynep Akata, Xinchen Yan, Lajanugen Lo-                    eswaranathan, and Surya Ganguli. Deep unsupervised
     geswaran, Bernt Schiele, and Honglak Lee. Generative ad-                   learning using nonequilibrium thermodynamics. CoRR,
     versarial text to image synthesis. In ICML, 2016. 4                        abs/1503.03585, 2015. 1, 3, 4, 18
[69] Danilo Jimenez Rezende, Shakir Mohamed, and Daan                      [83] Kihyuk Sohn, Honglak Lee, and Xinchen Yan. Learn-
     Wierstra. Stochastic backpropagation and approximate in-                   ing structured output representation using deep conditional
     ference in deep generative models. In Proceedings of the                   generative models. In C. Cortes, N. Lawrence, D. Lee,
     31st International Conference on International Conference                  M. Sugiyama, and R. Garnett, editors, Advances in Neural
     on Machine Learning, ICML, 2014. 1, 4, 29                                  Information Processing Systems, volume 28. Curran Asso-
[70] Robin Rombach, Patrick Esser, and Björn Ommer.                            ciates, Inc., 2015. 4
     Network-to-network translation with conditional invertible            [84] Jiaming Song, Chenlin Meng, and Stefano Ermon. Denois-
     neural networks. In NeurIPS, 2020. 3                                       ing diffusion implicit models. In ICLR. OpenReview.net,
[71] Olaf Ronneberger, Philipp Fischer, and Thomas Brox. U-                     2021. 3, 5, 6, 22
     net: Convolutional networks for biomedical image segmen-              [85] Yang Song, Jascha Sohl-Dickstein, Diederik P. Kingma,
     tation. In MICCAI (3), volume 9351 of Lecture Notes in                     Abhishek Kumar, Stefano Ermon, and Ben Poole. Score-
     Computer Science, pages 234–241. Springer, 2015. 2, 3, 4                   based generative modeling through stochastic differential
[72] Chitwan Saharia, Jonathan Ho, William Chan, Tim Sal-                       equations. CoRR, abs/2011.13456, 2020. 1, 3, 4, 18
     imans, David J. Fleet, and Mohammad Norouzi. Im-                      [86] Emma Strubell, Ananya Ganesh, and Andrew McCallum.
     age super-resolution via iterative refinement.         CoRR,               Energy and policy considerations for modern deep learn-
     abs/2104.07636, 2021. 1, 4, 8, 16, 22, 23, 27                              ing research. In The Thirty-Fourth AAAI Conference on
[73] Tim Salimans, Andrej Karpathy, Xi Chen, and Diederik P.                    Artificial Intelligence, AAAI 2020, The Thirty-Second In-
     Kingma. Pixelcnn++: Improving the pixelcnn with dis-                       novative Applications of Artificial Intelligence Conference,
     cretized logistic mixture likelihood and other modifications.              IAAI 2020, The Tenth AAAI Symposium on Educational
     CoRR, abs/1701.05517, 2017. 1, 3                                           Advances in Artificial Intelligence, EAAI 2020, New York,
[74] Dave Salvator. NVIDIA Developer Blog. https :                              NY, USA, February 7-12, 2020, pages 13693–13696. AAAI
     / / developer . nvidia . com / blog / getting -                            Press, 2020. 2


                                                                      12
 [87] Wei Sun and Tianfu Wu. Learning layout and style re-                      ference on Learning Representations, ICLR 2021, Virtual
      configurable gans for controllable image synthesis. CoRR,                 Event, Austria, May 3-7, 2021. OpenReview.net, 2021. 6
      abs/2003.11571, 2020. 22, 27                                        [101] Wilson Yan, Yunzhi Zhang, Pieter Abbeel, and Aravind
 [88] Roman Suvorov, Elizaveta Logacheva, Anton Mashikhin,                      Srinivas. Videogpt: Video generation using VQ-VAE and
      Anastasia Remizova, Arsenii Ashukha, Aleksei Silvestrov,                  transformers. CoRR, abs/2104.10157, 2021. 3
      Naejin Kong, Harshith Goka, Kiwoong Park, and Victor S.             [102] Fisher Yu, Yinda Zhang, Shuran Song, Ari Seff, and Jianx-
      Lempitsky. Resolution-robust large mask inpainting with                   iong Xiao. LSUN: construction of a large-scale image
      fourier convolutions. ArXiv, abs/2109.07161, 2021. 8, 9,                  dataset using deep learning with humans in the loop. CoRR,
      26, 32                                                                    abs/1506.03365, 2015. 5
 [89] Tristan Sylvain, Pengchuan Zhang, Yoshua Bengio, R. De-             [103] Jiahui Yu, Xin Li, Jing Yu Koh, Han Zhang, Ruoming Pang,
      von Hjelm, and Shikhar Sharma. Object-centric image gen-                  James Qin, Alexander Ku, Yuanzhong Xu, Jason Baldridge,
      eration from layouts. In Thirty-Fifth AAAI Conference on                  and Yonghui Wu. Vector-quantized image modeling with
      Artificial Intelligence, AAAI 2021, Thirty-Third Conference               improved vqgan, 2021. 3, 4
      on Innovative Applications of Artificial Intelligence, IAAI         [104] Jiahui Yu, Zhe L. Lin, Jimei Yang, Xiaohui Shen, Xin Lu,
      2021, The Eleventh Symposium on Educational Advances                      and Thomas S. Huang. Free-form image inpainting with
      in Artificial Intelligence, EAAI 2021, Virtual Event, Febru-              gated convolution. 2019 IEEE/CVF International Confer-
      ary 2-9, 2021, pages 2647–2655. AAAI Press, 2021. 20,                     ence on Computer Vision (ICCV), pages 4470–4479, 2019.
      22, 27                                                                    9
 [90] Patrick Tinsley, Adam Czajka, and Patrick Flynn. This face          [105] K. Zhang, Jingyun Liang, Luc Van Gool, and Radu Timo-
      does not exist... but it might be yours! identity leakage in              fte. Designing a practical degradation model for deep blind
      generative models. In Proceedings of the IEEE/CVF Win-                    image super-resolution. ArXiv, abs/2103.14006, 2021. 23
      ter Conference on Applications of Computer Vision, pages            [106] Richard Zhang, Phillip Isola, Alexei A. Efros, Eli Shecht-
      1320–1328, 2021. 9                                                        man, and Oliver Wang. The unreasonable effectiveness of
 [91] Antonio Torralba and Alexei A Efros. Unbiased look at                     deep features as a perceptual metric. In Proceedings of the
      dataset bias. In CVPR 2011, pages 1521–1528. IEEE, 2011.                  IEEE Conference on Computer Vision and Pattern Recog-
      9                                                                         nition (CVPR), June 2018. 3, 8, 19
 [92] Arash Vahdat and Jan Kautz. NVAE: A deep hierarchical               [107] Shengyu Zhao, Jianwei Cui, Yilun Sheng, Yue Dong, Xiao
      variational autoencoder. In NeurIPS, 2020. 3                              Liang, Eric I-Chao Chang, and Yan Xu. Large scale image
 [93] Arash Vahdat, Karsten Kreis, and Jan Kautz. Score-                        completion via co-modulated generative adversarial net-
      based generative modeling in latent space.            CoRR,               works. ArXiv, abs/2103.10428, 2021. 9
      abs/2106.05931, 2021. 2, 3, 5, 6                                    [108] Bolei Zhou, Àgata Lapedriza, Aditya Khosla, Aude Oliva,
 [94] Aaron van den Oord, Nal Kalchbrenner, Lasse Espeholt,                     and Antonio Torralba. Places: A 10 million image database
      koray kavukcuoglu, Oriol Vinyals, and Alex Graves. Con-                   for scene recognition. IEEE Transactions on Pattern Anal-
      ditional image generation with pixelcnn decoders. In Ad-                  ysis and Machine Intelligence, 40:1452–1464, 2018. 8, 9,
      vances in Neural Information Processing Systems, 2016. 3                  26
 [95] Aäron van den Oord, Nal Kalchbrenner, and Koray                    [109] Yufan Zhou, Ruiyi Zhang, Changyou Chen, Chunyuan Li,
      Kavukcuoglu. Pixel recurrent neural networks. CoRR,                       Chris Tensmeyer, Tong Yu, Jiuxiang Gu, Jinhui Xu, and
      abs/1601.06759, 2016. 3                                                   Tong Sun. LAFITE: towards language-free training for
 [96] Aäron van den Oord, Oriol Vinyals, and Koray                             text-to-image generation. CoRR, abs/2111.13792, 2021. 6,
      Kavukcuoglu. Neural discrete representation learning. In                  7, 16
      NIPS, pages 6306–6315, 2017. 2, 4, 29
 [97] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob
      Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser,
      and Illia Polosukhin. Attention is all you need. In NIPS,
      pages 5998–6008, 2017. 3, 4, 5, 7
 [98] Rivers Have Wings.               Tweet on Classifier-free
      guidance for autoregressive models.                https :
      / / twitter . com / RiversHaveWings / status /
      1478093658716966912, 2022. 6
 [99] Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chau-
      mond, Clement Delangue, Anthony Moi, Pierric Cistac,
      Tim Rault, Rémi Louf, Morgan Funtowicz, and Jamie
      Brew. Huggingface’s transformers: State-of-the-art natural
      language processing. CoRR, abs/1910.03771, 2019. 26
[100] Zhisheng Xiao, Karsten Kreis, Jan Kautz, and Arash Vah-
      dat. VAEBM: A symbiosis between variational autoen-
      coders and energy-based models. In 9th International Con-


                                                                     13
                                             Appendix




Figure 12. Convolutional samples from the semantic landscapes model as in Sec. 4.3.2, finetuned on 5122 images.


                                                      14
                                                     ’A painting of the last supper by Picasso.’




                                                                                                        ’An epic painting of Gandalf the Black
                          ’An oil painting of a latent space.’                                     summoning thunder and lightning in the mountains.’




                                                  ’A sunset over a mountain range, vector image.’




Figure 13. Combining classifier free diffusion guidance with the convolutional sampling strategy from Sec. 4.3.2, our 1.45B parameter
text-to-image model can be used for rendering images larger than the native 2562 resolution the model was trained on.



                                                                           15
A. Changelog
   Here we list changes between this version (https://arxiv.org/abs/2112.10752v2) of the paper and the
previous version, i.e. https://arxiv.org/abs/2112.10752v1.

  • We updated the results on text-to-image synthesis in Sec. 4.3 which were obtained by training a new, larger model (1.45B
    parameters). This also includes a new comparison to very recent competing methods on this task that were published on
    arXiv at the same time as ( [59, 109]) or after ( [26]) the publication of our work.
  • We updated results on class-conditional synthesis on ImageNet in Sec. 4.1, Tab. 3 (see also Sec. D.4) obtained by
    retraining the model with a larger batch size. The corresponding qualitative results in Fig. 26 and Fig. 27 were also
    updated. Both the updated text-to-image and the class-conditional model now use classifier-free guidance [32] as a
    measure to increase visual fidelity.
  • We conducted a user study (following the scheme suggested by Saharia et al [72]) which provides additional evaluation
    for our inpainting (Sec. 4.5) and superresolution models (Sec. 4.4).
  • Added Fig. 5 to the main paper, moved Fig. 18 to the appendix, added Fig. 13 to the appendix.

B. Detailed Information on Denoising Diffusion Models
                                                                                                 α2
   Diffusion models can be specified in terms of a signal-to-noise ratio SNR(t) = σ2t consisting of sequences (αt )Tt=1 and
                                                                                                   t
(σt )Tt=1 which, starting from a data sample x0 , define a forward diffusion process q as

                                                   q(xt |x0 ) = N (xt |αt x0 , σt2 I)                                        (4)

with the Markov structure for s < t:
                                                                                2
                                                 q(xt |xs ) = N (xt |αt|s xs , σt|s I)                                       (5)
                                                              αt
                                                      αt|s =                                                                 (6)
                                                              αs
                                                        2
                                                      σt|s  = σt2 − αt|s
                                                                      2
                                                                         σs2                                                 (7)

   Denoising diffusion models are generative models p(x0 ) which revert this process with a similar Markov structure running
backward in time, i.e. they are specified as
                                                            Z              T
                                                                           Y
                                                p(x0 ) =          p(xT )         p(xt−1 |xt )                                (8)
                                                              z            t=1

The evidence lower bound (ELBO) associated with this model then decomposes over the discrete time steps as
                                                                    T
                                                                    X
                    − log p(x0 ) ≤ KL(q(xT |x0 )|p(xT )) +                 Eq(xt |x0 ) KL(q(xt−1 |xt , x0 )|p(xt−1 |xt ))    (9)
                                                                    t=1

The prior p(xT ) is typically choosen as a standard normal distribution and the first term of the ELBO then depends only on
the final signal-to-noise ratio SNR(T ). To minimize the remaining terms, a common choice to parameterize p(xt−1 |xt ) is to
specify it in terms of the true posterior q(xt−1 |xt , x0 ) but with the unknown x0 replaced by an estimate xθ (xt , t) based on
the current step xt . This gives [45]

                                        p(xt−1 |xt ) := q(xt−1 |xt , xθ (xt , t))                                           (10)
                                                                                       2
                                                                                2     σt−1
                                                       = N (xt−1 |µθ (xt , t), σt|t−1      I),                              (11)
                                                                                       σt2
where the mean can be expressed as
                                                               2                      2
                                                       αt|t−1 σt−1      αt−1 σt|t−1
                                       µθ (xt , t) =         2     xt +             xθ (xt , t).                            (12)
                                                           σt              σt2

                                                                     16
In this case, the sum of the ELBO simplify to
    T                                                   T
    X                                                   X             1
          Eq(xt |x0 ) KL(q(xt−1 |xt , x0 )|p(xt−1 ) =       EN (|0,I) (SNR(t − 1) − SNR(t))kx0 − xθ (αt x0 + σt , t)k2   (13)
    t=1                                                 t=1
                                                                      2

Following [30], we use the reparameterization

                                                 θ (xt , t) = (xt − αt xθ (xt , t))/σt                                    (14)

to express the reconstruction term as a denoising objective,

                                                                     σt2
                                    kx0 − xθ (αt x0 + σt , t)k2 =       k − θ (αt x0 + σt , t)k2                       (15)
                                                                     αt2

and the reweighting, which assigns each of the terms the same weight and results in Eq. (1).




                                                                   17
C. Image Guiding Mechanisms


                    Samples 2562             Guided Convolutional Samples 5122 Convolutional Samples 5122




Figure 14. On landscapes, convolutional sampling with unconditional models can lead to homogeneous and incoherent global structures
(see column 2). L2 -guiding with a low resolution image can help to reestablish coherent global structures.


   An intriguing feature of diffusion models is that unconditional models can be conditioned at test-time [15, 82, 85]. In
particular, [15] presented an algorithm to guide both unconditional and conditional models trained on the ImageNet dataset
with a classifier log pΦ (y|xt ), trained on each xt of the diffusion process. We directly build on this formulation and introduce
post-hoc image-guiding:
   For an epsilon-parameterized model with fixed variance, the guiding algorithm as introduced in [15] reads:
                                                              q
                                         ˆ ← θ (zt , t) +    1 − αt2 ∇zt log pΦ (y|zt ) .                                   (16)

   This can be interpreted as an update correcting the “score” θ with a conditional distribution log pΦ (y|zt ).
   So far, this scenario has only been applied to single-class classification models. We re-interpret the guiding distribution
pΦ (y|T (D(z0 (zt )))) as a general purpose image-to-image translation task given a target image y, where T can be any
differentiable transformation adopted to the image-to-image translation task at hand, such as the identity, a downsampling
operation or similar.


                                                                   18
As an example, we can assume a Gaussian guider with fixed variance σ 2 = 1, such that
                                                          1
                                        log pΦ (y|zt ) = − ky − T (D(z0 (zt )))k22                                 (17)
                                                          2
becomes a L2 regression objective.
   Fig. 14 demonstrates how this formulation can serve as an upsampling mechanism of an unconditional model trained on
2562 images, where unconditional samples of size 2562 guide the convolutional synthesis of 5122 images and T is a 2×
bicubic downsampling. Following this motivation, we also experiment with a perceptual similarity guiding and replace the
L2 objective with the LPIPS [106] metric, see Sec. 4.4.




                                                           19
D. Additional Results
D.1. Choosing the Signal-to-Noise Ratio for High-Resolution Synthesis

           KL-reg, w/o rescaling                             KL-reg, w/ rescaling                           VQ-reg, w/o rescaling




Figure 15. Illustrating the effect of latent space rescaling on convolutional sampling, here for semantic image synthesis on landscapes. See
Sec. 4.3.2 and Sec. D.1.

   As discussed in Sec. 4.3.2, the signal-to-noise ratio induced by the variance of the latent space (i.e. Var(z)/σt2 ) significantly
affects the results for convolutional sampling. For example, when training a LDM directly in the latent space of a KL-
regularized model (see Tab. 8), this ratio is very high, such that the model allocates a lot of semantic detail early on in the
reverse denoising process. In contrast, when rescaling the latent space by the component-wise standard deviation of the
latents as described in Sec. G, the SNR is descreased. We illustrate the effect on convolutional sampling for semantic image
synthesis in Fig. 15. Note that the VQ-regularized space has a variance close to 1, such that it does not have to be rescaled.

D.2. Full List of all First Stage Models
   We provide a complete list of various autoenconding models trained on the OpenImages dataset in Tab. 8.

D.3. Layout-to-Image Synthesis
    Here we provide the quantitative evaluation and additional samples for our layout-to-image models from Sec. 4.3.1. We
train a model on the COCO [4] and one on the OpenImages [49] dataset, which we subsequently additionally finetune on
COCO. Tab 9 shows the result. Our COCO model reaches the performance of recent state-of-the art models in layout-to-
image synthesis, when following their training and evaluation protocol [89]. When finetuning from the OpenImages model,
we surpass these works. Our OpenImages model surpasses the results of Jahn et al [37] by a margin of nearly 11 in terms of
FID. In Fig. 16 we show additional samples of the model finetuned on COCO.

D.4. Class-Conditional Image Synthesis on ImageNet
   Tab. 10 contains the results for our class-conditional LDM measured in FID and Inception score (IS). LDM-8 requires
significantly fewer parameters and compute requirements (see Tab. 18) to achieve very competitive performance. Similar
to previous work, we can further boost the performance by training a classifier on each noise scale and guiding with it,


                                                                    20
                         f           |Z|      c    R-FID ↓      R-IS ↑        PSNR ↑        PSIM ↓       SSIM ↑
                   16 VQGAN [23]    16384    256      4.98           –        19.9 ±3.4    1.83 ±0.42   0.51 ±0.18
                   16 VQGAN [23]     1024    256      7.94           –        19.4 ±3.3    1.98 ±0.43   0.50 ±0.18
                    8 DALL-E [66]   8192      -      32.01           –        22.8 ±2.1    1.95 ±0.51   0.73 ±0.13
                         32         16384    16      31.83     40.40 ±1.07   17.45 ±2.90   2.58 ±0.48   0.41 ±0.18
                         16         16384     8       5.15    144.55 ±3.74   20.83 ±3.61   1.73 ±0.43   0.54 ±0.18
                         8          16384     4      1.14     201.92 ±3.97   23.07 ±3.99   1.17 ±0.36   0.65 ±0.16
                         8            256     4      1.49     194.20 ±3.87   22.35 ±3.81   1.26 ±0.37   0.62 ±0.16
                         4           8192     3      0.58     224.78 ±5.35   27.43 ±4.26   0.53 ±0.21   0.82 ±0.10
                         4†          8192     3      1.06     221.94 ±4.58   25.21 ±4.17   0.72 ±0.26   0.76 ±0.12
                         4           256     3       0.47     223.81 ±4.58   26.43 ±4.22   0.62 ±0.24   0.80 ±0.11
                         2          2048     2       0.16     232.75 ±5.09   30.85 ±4.12   0.27 ±0.12   0.91 ±0.05
                         2            64     2       0.40     226.62 ±4.83   29.13 ±3.46   0.38 ±0.13   0.90 ±0.05
                         32           KL     64       2.04    189.53 ±3.68   22.27 ±3.93   1.41 ±0.40   0.61 ±0.17
                         32           KL     16        7.3    132.75 ±2.71   20.38 ±3.56   1.88 ±0.45   0.53 ±0.18
                         16           KL     16       0.87    210.31 ±3.97   24.08 ±4.22   1.07 ±0.36   0.68 ±0.15
                         16           KL      8       2.63    178.68 ±4.08   21.94 ±3.92   1.49 ±0.42   0.59 ±0.17
                         8            KL      4      0.90     209.90 ±4.92   24.19 ±4.19   1.02 ±0.35   0.69 ±0.15
                         4            KL      3      0.27     227.57 ±4.89   27.53 ±4.54   0.55 ±0.24   0.82 ±0.11
                         2            KL      2      0.086    232.66 ±5.16   32.47 ±4.19   0.20 ±0.09   0.93 ±0.04

   Table 8. Complete autoencoder zoo trained on OpenImages, evaluated on ImageNet-Val. † denotes an attention-free autoencoder.


                                        layout-to-image synthesis on the COCO dataset




Figure 16. More samples from our best model for layout-to-image synthesis, LDM-4, which was trained on the OpenImages dataset and
finetuned on the COCO dataset. Samples generated with 100 DDIM steps and η = 0. Layouts are from the COCO validation set.


see Sec. C. Unlike the pixel-based methods, this classifier is trained very cheaply in latent space. For additional qualitative
results, see Fig. 26 and Fig. 27.


                                                                21
                                                       COCO256 × 256        OpenImages 256 × 256            OpenImages 512 × 512
                      Method                                 FID↓                     FID↓                             FID↓
                      LostGAN-V2 [87]                       42.55                       -                                -
                      OC-GAN [89]                           41.65                       -                                -
                      SPADE [62]                            41.11                       -                                -
                      VQGAN+T [37]                          56.58                     45.33                            48.11
                      LDM-8 (100 steps, ours)               42.06†                      -                                -
                      LDM-4 (200 steps, ours)               40.91∗                    32.02                            35.80

Table 9. Quantitative comparison of our layout-to-image models on the COCO [4] and OpenImages [49] datasets. † : Training from scratch
on COCO; ∗ : Finetuning from OpenImages.


 Method             FID↓       IS↑        Precision↑    Recall↑   Nparams
 SR3 [72]           11.30        -            -            -         625M                                               -
 ImageBART [21]     21.19        -            -            -         3.5B                                               -
 ImageBART [21]      7.44        -            -            -         3.5B                                        0.05 acc. rate∗
 VQGAN+T [23]       17.04     70.6±1.8        -            -         1.3B                                               -
 VQGAN+T [23]        5.88    304.8±3.6        -            -         1.3B                                        0.05 acc. rate∗
 BigGan-deep [3]    6.95     203.6±2.6      0.87         0.28        340M                                               -
 ADM [15]           10.94     100.98        0.69         0.63        554M                                       250 DDIM steps
 ADM-G [15]         4.59       186.7        0.82         0.52        608M                                       250 DDIM steps
 ADM-G,ADM-U [15]    3.85     221.72        0.84         0.53         n/a                                     2 × 250 DDIM steps
 CDM [31]            4.88   158.71±2.26       -            -          n/a                                     2 × 100 DDIM steps
 LDM-8 (ours)       17.41    72.92±2.6      0.65         0.62        395M                      200 DDIM steps, 2.9M train steps, batch size 64
 LDM-8-G (ours)     8.11    190.43±2.60     0.83         0.36        506M            200 DDIM steps, classifier scale 10, 2.9M train steps, batch size 64
 LDM-8 (ours)       15.51    79.03±1.03     0.65         0.63        395M                      200 DDIM steps, 4.8M train steps, batch size 64
 LDM-8-G (ours)     7.76    209.52±4.24     0.84         0.35        506M            200 DDIM steps, classifier scale 10, 4.8M train steps, batch size 64
 LDM-4 (ours)       10.56   103.49±1.24     0.71         0.62        400M                     250 DDIM steps, 178K train steps, batch size 1200
 LDM-4-G (ours)     3.95    178.22±2.43     0.81         0.55        400M   250 DDIM steps, unconditional guidance [32] scale 1.25, 178K train steps, batch size 1200
 LDM-4-G (ours)      3.60   247.67±5.59     0.87         0.48        400M   250 DDIM steps, unconditional guidance [32] scale 1.5, 178K train steps, batch size 1200


Table 10. Comparison of a class-conditional ImageNet LDM with recent state-of-the-art methods for class-conditional image generation
on the ImageNet [12] dataset.∗ : Classifier rejection sampling with the given rejection rate as proposed in [67].



D.5. Sample Quality vs. V100 Days (Continued from Sec. 4.1)




Figure 17. For completeness we also report the training progress of class-conditional LDMs on the ImageNet dataset for a fixed number
of 35 V100 days. Results obtained with 100 DDIM steps [84] and κ = 0. FIDs computed on 5000 samples for efficiency reasons.


   For the assessment of sample quality over the training progress in Sec. 4.1, we reported FID and IS scores as a function
of train steps. Another possibility is to report these metrics over the used resources in V100 days. Such an analysis is
additionally provided in Fig. 17, showing qualitatively similar results.


                                                                            22
                                  Method                                   FID ↓           IS ↑        PSNR ↑       SSIM ↑
                                  Image Regression [72]                     15.2          121.1          27.9        0.801
                                  SR3 [72]                                  5.2           180.1          26.4        0.762
                                  LDM-4 (ours, 100 steps)                2.8† /4.8‡       166.3        24.4±3.8     0.69±0.14
                                  LDM-4 (ours, 50 steps, guiding)        4.4† /6.4‡       153.7        25.8±3.7     0.74±0.12
                                  LDM-4 (ours, 100 steps, guiding)       4.4† /6.4‡       154.1        25.7±3.7     0.73±0.12
                                  LDM-4 (ours, 100 steps, +15 ep.)      2.6† / 4.6‡    169.76±5.03     24.4±3.8     0.69±0.14
                                  Pixel-DM (100 steps, +15 ep.)         5.1† / 7.1‡    163.06±4.67     24.1±3.3     0.59±0.12
Table 11. ×4 upscaling results on ImageNet-Val. (2562 ); † : FID features computed on validation split, ‡ : FID features computed on train
split. We also include a pixel-space baseline that receives the same amount of compute as LDM-4. The last two rows received 15 epochs
of additional training compared to the former results.


D.6. Super-Resolution
   For better comparability between LDMs and diffusion models in pixel space, we extend our analysis from Tab. 5 by
comparing a diffusion model trained for the same number of steps and with a comparable number 1 of parameters to our
LDM. The results of this comparison are shown in the last two rows of Tab. 11 and demonstrate that LDM achieves better
performance while allowing for significantly faster sampling. A qualitative comparison is given in Fig. 20 which shows
random samples from both LDM and the diffusion model in pixel space.

D.6.1    LDM-BSR: General Purpose SR Model via Diverse Image Degradation

                     bicubic                                              LDM-SR                                                LDM-BSR




Figure 18. LDM-BSR generalizes to arbitrary inputs and can be used as a general-purpose upsampler, upscaling samples from a class-
conditional LDM (image cf . Fig. 4) to 10242 resolution. In contrast, using a fixed degradation process (see Sec. 4.4) hinders generalization.
   To evaluate generalization of our LDM-SR, we apply it both on synthetic LDM samples from a class-conditional ImageNet
model (Sec. 4.1) and images crawled from the internet. Interestingly, we observe that LDM-SR, trained only with a bicubicly
downsampled conditioning as in [72], does not generalize well to images which do not follow this pre-processing. Hence, to
obtain a superresolution model for a wide range of real world images, which can contain complex superpositions of camera
noise, compression artifacts, blurr and interpolations, we replace the bicubic downsampling operation in LDM-SR with the
degration pipeline from [105]. The BSR-degradation process is a degradation pipline which applies JPEG compressions
noise, camera sensor noise, different image interpolations for downsampling, Gaussian blur kernels and Gaussian noise in a
random order to an image. We found that using the bsr-degredation process with the original parameters as in [105] leads to
a very strong degradation process. Since a more moderate degradation process seemed apppropiate for our application, we
adapted the parameters of the bsr-degradation (our adapted degradation process can be found in our code base at https:
//github.com/CompVis/latent-diffusion). Fig. 18 illustrates the effectiveness of this approach by directly
comparing LDM-SR with LDM-BSR. The latter produces images much sharper than the models confined to a fixed pre-
processing, making it suitable for real-world applications. Further results of LDM-BSR are shown on LSUN-cows in Fig. 19.
   1 It is not possible to exactly match both architectures since the diffusion model operates in the pixel space




                                                                              23
E. Implementation Details and Hyperparameters
E.1. Hyperparameters
   We provide an overview of the hyperparameters of all trained LDM models in Tab. 12, Tab. 13, Tab. 14 and Tab. 15.

                                      CelebA-HQ 256 × 256     FFHQ 256 × 256      LSUN-Churches 256 × 256      LSUN-Bedrooms 256 × 256
              f                                 4                      4                          8                          4
              z-shape                     64 × 64 × 3           64 × 64 × 3                       -                   64 × 64 × 3
              |Z|                             8192                  8192                          -                       8192
              Diffusion steps                 1000                  1000                       1000                       1000
              Noise Schedule                 linear                linear                     linear                     linear
              Nparams                        274M                  274M                       294M                       274M
              Channels                        224                    224                        192                        224
              Depth                             2                      2                          2                          2
              Channel Multiplier            1,2,3,4               1,2,3,4                    1,2,2,4,4                  1,2,3,4
              Attention resolutions        32, 16, 8             32, 16, 8                  32, 16, 8, 4               32, 16, 8
              Head Channels                    32                     32                         24                         32
              Batch Size                       48                     42                         96                         48
              Iterations∗                     410k                  635k                       500k                      1.9M
              Learning Rate                  9.6e-5                8.4e-5                      5.e-5                     9.6e-5



Table 12. Hyperparameters for the unconditional LDMs producing the numbers shown in Tab. 1. All models trained on a single NVIDIA
A100.



                                            LDM-1              LDM-2             LDM-4             LDM-8       LDM-16         LDM-32
              z-shape                    256 × 256 × 3      128 × 128 × 2      64 × 64 × 3      32 × 32 × 4   16 × 16 × 8   88 × 8 × 32
              |Z|                               -                2048             8192             16384         16384         16384
              Diffusion steps                 1000               1000             1000              1000          1000          1000
              Noise Schedule                 linear             linear            linear           linear        linear        linear
              Model Size                     396M               391M              391M             395M          395M          395M
              Channels                         192                192              192               256           256           256
              Depth                             2                  2                 2                 2            2             2
              Channel Multiplier           1,1,2,2,4,4        1,2,2,4,4          1,2,3,5            1,2,4         1,2,4         1,2,4
              Number of Heads                   1                  1                 1                 1            1             1
              Batch Size                        7                  9                40                64           112           112
              Iterations                       2M                 2M                2M               2M            2M            2M
              Learning Rate                  4.9e-5             6.3e-5             8e-5            6.4e-5        4.5e-5        4.5e-5
              Conditioning                    CA                CA                CA                CA            CA            CA
              CA-resolutions                32, 16, 8         32, 16, 8         32, 16, 8         32, 16, 8     16, 8, 4       8, 4, 2
              Embedding Dimension             512               512               512               512           512           512
              Transformers Depth                1                 1                 1                 1            1              1



Table 13. Hyperparameters for the conditional LDMs trained on the ImageNet dataset for the analysis in Sec. 4.1. All models trained on a
single NVIDIA A100.



E.2. Implementation Details
E.2.1   Implementations of τθ for conditional LDMs

For the experiments on text-to-image and layout-to-image (Sec. 4.3.1) synthesis, we implement the conditioner τθ as an
unmasked transformer which processes a tokenized version of the input y and produces an output ζ := τθ (y), where ζ ∈
RM ×dτ . More specifically, the transformer is implemented from N transformer blocks consisting of global self-attention
layers, layer-normalization and position-wise MLPs as follows2 :

  2 adapted from https://github.com/lucidrains/x-transformers




                                                                          24
                                             LDM-1               LDM-2            LDM-4            LDM-8             LDM-16          LDM-32
                z-shape                   256 × 256 × 3      128 × 128 × 2     64 × 64 × 3       32 × 32 × 4      16 × 16 × 8       88 × 8 × 32
                |Z|                              -                2048             8192             16384            16384             16384
                Diffusion steps                1000               1000             1000              1000             1000              1000
                Noise Schedule                linear             linear           linear            linear           linear            linear
                Model Size                    270M               265M             274M              258M             260M              258M
                Channels                       192                 192              224               256              256               256
                Depth                            2                   2                2                 2               2                 2
                Channel Multiplier          1,1,2,2,4,4        1,2,2,4,4         1,2,3,4             1,2,4            1,2,4             1,2,4
                Attention resolutions        32, 16, 8         32, 16, 8        32, 16, 8         32, 16, 8         16, 8, 4           8, 4, 2
                Head Channels                   32                  32               32                32               32                32
                Batch Size                       9                  11               48                96              128               128
                Iterations∗                    500k               500k             500k              500k             500k              500k
                Learning Rate                  9e-5              1.1e-4           9.6e-5            9.6e-5           1.3e-4            1.3e-4


Table 14. Hyperparameters for the unconditional LDMs trained on the CelebA dataset for the analysis in Fig. 7. All models trained on a
single NVIDIA A100. ∗ : All models are trained for 500k iterations. If converging earlier, we used the best checkpoint for assessing the
provided FID scores.

    Task                   Text-to-Image         Layout-to-Image          Class-Label-to-Image    Super Resolution     Inpainting    Semantic-Map-to-Image
    Dataset                   LAION         OpenImages        COCO             ImageNet              ImageNet           Places            Landscapes
    f                             8               4                8                4                     4                 4                    8
    z-shape                 32 × 32 × 4     64 × 64 × 3     32 × 32 × 4       64 × 64 × 3           64 × 64 × 3       64 × 64 × 3         32 × 32 × 4
    |Z|                           -             8192           16384              8192                  8192              8192               16384
    Diffusion steps             1000            1000            1000              1000                  1000              1000                1000
    Noise Schedule             linear          linear          linear            linear                linear            linear              linear
    Model Size                 1.45B           306M            345M              395M                  169M              215M                215M
    Channels                     320             128             192               192                   160               128                 128
    Depth                         2               2               2                 2                      2                2                    2
    Channel Multiplier        1,2,4,4         1,2,3,4           1,2,4           1,2,3,5               1,2,2,4             1,4,8               1,4,8
    Number of Heads               8                1               1                1                      1                1                    1
    Dropout                       -                -             0.1                -                      -                -                    -
    Batch Size                   680              24              48              1200                    64               128                  48
    Iterations                 390K            4.4M            170K              178K                  860K              360K                360K
    Learning Rate              1.0e-4          4.8e-5          4.8e-5            1.0e-4                6.4e-5            1.0e-6              4.8e-5
    Conditioning                 CA             CA              CA               CA                   concat            concat              concat
    (C)A-resolutions          32, 16, 8       32, 16, 8       32, 16, 8        32, 16, 8                -                 -                   -
    Embedding Dimension         1280            512             512              512                    -                 -                   -
    Transformer Depth             1               3               2                1                    -                 -                   -



Table 15. Hyperparameters for the conditional LDMs from Sec. 4. All models trained on a single NVIDIA A100 except for the inpainting
model which was trained on eight V100.




                                                    ζ ← TokEmb(y) + PosEmb(y)                                                                                (18)
                                                    for i = 1, . . . , N :
                                                          ζ1 ← LayerNorm(ζ)                                                                                  (19)
                                                          ζ2 ← MultiHeadSelfAttention(ζ1 ) + ζ                                                               (20)
                                                          ζ3 ← LayerNorm(ζ2 )                                                                                (21)
                                                          ζ ← MLP(ζ3 ) + ζ2                                                                                  (22)
                                                    ζ ← LayerNorm(ζ)                                                                                         (23)
                                                                                                                                                             (24)

   With ζ available, the conditioning is mapped into the UNet via the cross-attention mechanism as depicted in Fig. 3. We
modify the “ablated UNet” [15] architecture and replace the self-attention layer with a shallow (unmasked) transformer
consisting of T blocks with alternating layers of (i) self-attention, (ii) a position-wise MLP and (iii) a cross-attention layer;


                                                                             25
see Tab. 16. Note that without (ii) and (iii), this architecture is equivalent to the “ablated UNet”.
   While it would be possible to increase the representational power of τθ by additionally conditioning on the time step t, we
do not pursue this choice as it reduces the speed of inference. We leave a more detailed analysis of this modification to future
work.
   For the text-to-image model, we rely on a publicly available3 tokenizer [99]. The layout-to-image model discretizes the
spatial locations of the bounding boxes and encodes each box as a (l, b, c)-tuple, where l denotes the (discrete) top-left and b
the bottom-right position. Class information is contained in c.
See Tab. 17 for the hyperparameters of τθ and Tab. 13 for those of the UNet for both of the above tasks.

   Note that the class-conditional model as described in Sec. 4.1 is also implemented via cross-attention, where τθ is a single
learnable embedding layer with a dimensionality of 512, mapping classes y to ζ ∈ R1×512 .

                                                   input                     Rh×w×c
                                                   LayerNorm                Rh×w×c
                                                   Conv1x1                 Rh×w×d·nh
                                                   Reshape                 Rh·w×d·nh
                                                                           Rh·w×d·nh
                                                       
                                                       SelfAttention
                                                       
                                                    ×T       MLP           Rh·w×d·nh
                                                                          Rh·w×d·nh
                                                         CrossAttention
                                                         
                                                   Reshape                 Rh×w×d·nh
                                                   Conv1x1                  Rh×w×c



Table 16. Architecture of a transformer block as described in Sec. E.2.1, replacing the self-attention layer of the standard “ablated UNet”
architecture [15]. Here, nh denotes the number of attention heads and d the dimensionality per head.



                                                           Text-to-Image     Layout-to-Image
                                         seq-length             77                    92
                                         depth N                32                   16
                                         dim                   1280                  512


                         Table 17. Hyperparameters for the experiments with transformer encoders in Sec. 4.3.



E.2.2   Inpainting
For our experiments on image-inpainting in Sec. 4.5, we used the code of [88] to generate synthetic masks. We use a fixed
set of 2k validation and 30k testing samples from Places [108]. During training, we use random crops of size 256 × 256
and evaluate on crops of size 512 × 512. This follows the training and testing protocol in [88] and reproduces their reported
metrics (see † in Tab. 7). We include additional qualitative results of LDM-4, w/ attn in Fig. 21 and of LDM-4, w/o attn, big,
w/ ft in Fig. 22.
E.3. Evaluation Details
This section provides additional details on evaluation for the experiments shown in Sec. 4.

E.3.1   Quantitative Results in Unconditional and Class-Conditional Image Synthesis
We follow common practice and estimate the statistics for calculating the FID-, Precision- and Recall-scores [29,50] shown in
Tab. 1 and 10 based on 50k samples from our models and the entire training set of each of the shown datasets. For calculating
FID scores we use the torch-fidelity package [60]. However, since different data processing pipelines might lead to
different results [64], we also evaluate our models with the script provided by Dhariwal and Nichol [15]. We find that results
   3 https://huggingface.co/transformers/model_doc/bert.html#berttokenizerfast




                                                                      26
mainly coincide, except for the ImageNet and LSUN-Bedrooms datasets, where we notice slightly varying scores of 7.76
(torch-fidelity) vs. 7.77 (Nichol and Dhariwal) and 2.95 vs 3.0. For the future we emphasize the importance of a
unified procedure for sample quality assessment. Precision and Recall are also computed by using the script provided by
Nichol and Dhariwal.

E.3.2   Text-to-Image Synthesis
Following the evaluation protocol of [66] we compute FID and Inception Score for the Text-to-Image models from Tab. 2 by
comparing generated samples with 30000 samples from the validation set of the MS-COCO dataset [51]. FID and Inception
Scores are computed with torch-fidelity.

E.3.3   Layout-to-Image Synthesis
For assessing the sample quality of our Layout-to-Image models from Tab. 9 on the COCO dataset, we follow common
practice [37, 87, 89] and compute FID scores the 2048 unaugmented examples of the COCO Segmentation Challenge split.
To obtain better comparability, we use the exact same samples as in [37]. For the OpenImages dataset we similarly follow
their protocol and use 2048 center-cropped test images from the validation set.

E.3.4   Super Resolution
We evaluate the super-resolution models on ImageNet following the pipeline suggested in [72], i.e. images with a shorter
size less than 256 px are removed (both for training and evaluation). On ImageNet, the low-resolution images are produced
using bicubic interpolation with anti-aliasing. FIDs are evaluated using torch-fidelity [60], and we produce samples
on the validation split. For FID scores, we additionally compare to reference features computed on the train split, see Tab. 5
and Tab. 11.

E.3.5   Efficiency Analysis
For efficiency reasons we compute the sample quality metrics plotted in Fig. 6, 17 and 7 based on 5k samples. Therefore,
the results might vary from those shown in Tab. 1 and 10. All models have a comparable number of parameters as provided
in Tab. 13 and 14. We maximize the learning rates of the individual models such that they still train stably. Therefore, the
learning rates slightly vary between different runs cf . Tab. 13 and 14.

E.3.6   User Study
For the results of the user study presented in Tab. 4 we followed the protocoll of [72] and and use the 2-alternative force-choice
paradigm to assess human preference scores for two distinct tasks. In Task-1 subjects were shown a low resolution/masked
image between the corresponding ground truth high resolution/unmasked version and a synthesized image, which was gen-
erated by using the middle image as conditioning. For SuperResolution subjects were asked: ’Which of the two images is a
better high quality version of the low resolution image in the middle?’. For Inpainting we asked ’Which of the two images
contains more realistic inpainted regions of the image in the middle?’. In Task-2, humans were similarly shown the low-
res/masked version and asked for preference between two corresponding images generated by the two competing methods.
As in [72] humans viewed the images for 3 seconds before responding.




                                                               27
F. Computational Requirements

    Method                                                                                           Generator   Classifier    Overall    Inference    Nparams   FID↓        IS↑        Precision↑   Recall↑
                                                                                                     Compute     Compute      Compute    Throughput∗

    LSUN Churches 2562
    StyleGAN2 [42]†                                                                                     64           -          64            -         59M      3.86          -            -           -
    LDM-8 (ours, 100 steps, 410K)                                                                       18           -          18          6.80        256M     4.02          -          0.64        0.52

    LSUN Bedrooms 2562
    ADM [15]† (1000 steps)                                                                             232           -          232         0.03        552M     1.9           -          0.66        0.51
    LDM-4 (ours, 200 steps, 1.9M)                                                                       60           -          55          1.07        274M     2.95          -          0.66        0.48

    CelebA-HQ 2562
    LDM-4 (ours, 500 steps, 410K)                                                                      14.4          -          14.4        0.43        274M     5.11          -          0.72        0.49

    FFHQ 2562
    StyleGAN2 [42]                                                                                    32.13‡         -         32.13†         -          59M      3.8          -            -           -
    LDM-4 (ours, 200 steps, 635K)                                                                       26           -           26         1.07        274M     4.98          -          0.73        0.50

    ImageNet 2562
    VQGAN-f-4 (ours, first stage)                                                                       29           -          29            -         55M      0.58††        -            -           -
    VQGAN-f-8 (ours, first stage)                                                                       66           -          66            -         68M      1.14††        -            -           -
                     †
    BigGAN-deep [3]                                                                                  128-256                  128-256         -         340M     6.95      203.6±2.6      0.87        0.28
    ADM [15] (250 steps) †                                                                             916           -          916         0.12        554M     10.94      100.98        0.69        0.63
    ADM-G [15] (25 steps) †                                                                            916          46          962          0.7        608M      5.58         -          0.81        0.49
    ADM-G [15] (250 steps)†                                                                            916          46          962         0.07        608M      4.59       186.7        0.82        0.52
    ADM-G,ADM-U [15] (250 steps)†                                                                      329          30          349          n/a         n/a      3.85      221.72        0.84        0.53
    LDM-8-G (ours, 100, 2.9M)                                                                           79          12           91         1.93        506M      8.11     190.4±2.6      0.83        0.36
    LDM-8 (ours, 200 ddim steps 2.9M, batch size 64)                                                    79           -           79          1.9        395M     17.41       72.92        0.65        0.62
    LDM-4 (ours, 250 ddim steps 178K, batch size 1200)                                                 271           -          271          0.7        400M     10.56    103.49±1.24     0.71        0.62
    LDM-4-G (ours, 250 ddim steps 178K, batch size 1200, classifier-free guidance [32] scale 1.25)     271           -          271          0.4        400M      3.95    178.22±2.43     0.81        0.55
    LDM-4-G (ours, 250 ddim steps 178K, batch size 1200, classifier-free guidance [32] scale 1.5)      271           -          271          0.4        400M      3.60    247.67±5.59     0.87        0.48




Table 18. Comparing compute requirements during training and inference throughput with state-of-the-art generative models. Compute
during training in V100-days, numbers of competing methods taken from [15] unless stated differently;∗ : Throughput measured in sam-
ples/sec on a single NVIDIA A100;† : Numbers taken from [15] ;‡ : Assumed to be trained on 25M train examples; †† : R-FID vs. ImageNet
validation set

   In Tab 18 we provide a more detailed analysis on our used compute ressources and compare our best performing models
on the CelebA-HQ, FFHQ, LSUN and ImageNet datasets with the recent state of the art models by using their provided
numbers, cf . [15]. As they report their used compute in V100 days and we train all our models on a single NVIDIA A100
GPU, we convert the A100 days to V100 days by assuming a ×2.2 speedup of A100 vs V100 [74]4 . To assess sample quality,
we additionally report FID scores on the reported datasets. We closely reach the performance of state of the art methods as
StyleGAN2 [42] and ADM [15] while significantly reducing the required compute resources.




  4 This factor corresponds to the speedup of the A100 over the V100 for a U-Net, as defined in Fig. 1 in [74]




                                                                                                       28
G. Details on Autoencoder Models
    We train all our autoencoder models in an adversarial manner following [23], such that a patch-based discriminator Dψ
is optimized to differentiate original images from reconstructions D(E(x)). To avoid arbitrarily scaled latent spaces, we
regularize the latent z to be zero centered and obtain small variance by introducing an regularizing loss term Lreg .
We investigate two different regularization methods: (i) a low-weighted Kullback-Leibler-term between qE (z|x) =
N (z; Eµ , Eσ2 ) and a standard normal distribution N (z; 0, 1) as in a standard variational autoencoder [46, 69], and, (ii) regu-
larizing the latent space with a vector quantization layer by learning a codebook of |Z| different exemplars [96].
To obtain high-fidelity reconstructions we only use a very small regularization for both scenarios, i.e. we either weight the
KL term by a factor ∼ 10−6 or choose a high codebook dimensionality |Z|.
    The full objective to train the autoencoding model (E, D) reads:
                                                                                                               
                 LAutoencoder = min max Lrec (x, D(E(x))) − Ladv (D(E(x))) + log Dψ (x) + Lreg (x; E, D)                      (25)
                               E,D   ψ


DM Training in Latent Space Note that for training diffusion models on the learned latent space, we again distinguish two
cases when learning p(z) or p(z|y) (Sec. 4.3): (i) For a KL-regularized latent space, we sample z = Eµ (x)+Eσ (x)·ε =: E(x),
where ε ∼ N (0, 1). When rescaling the latent, we estimate the component-wise variance
                                                          1  X
                                               σ̂ 2 =          (z b,c,h,w − µ̂)2
                                                        bchw
                                                             b,c,h,w

                                               1              b,c,h,w
                                                    P
from the first batch in the data, where µ̂ = bchw   b,c,h,w z         . The output of E is scaled such that the rescaled latent has
                                  z   E(x)
unit standard deviation, i.e. z ← σ̂ = σ̂ . (ii) For a VQ-regularized latent space, we extract z before the quantization layer
and absorb the quantization operation into the decoder, i.e. it can be interpreted as the first layer of D.

H. Additional Qualitative Results
  Finally, we provide additional qualitative results for our landscapes model (Fig. 12, 23, 24 and 25), our class-conditional
ImageNet model (Fig. 26 - 27) and our unconditional models for the CelebA-HQ, FFHQ and LSUN datasets (Fig. 28 - 31).
Similar as for the inpainting model in Sec. 4.5 we also fine-tuned the semantic landscapes model from Sec. 4.3.2 directly on
5122 images and depict qualitative results in Fig. 12 and Fig. 23. For our those models trained on comparably small datasets,
we additionally show nearest neighbors in VGG [79] feature space for samples from our models in Fig. 32 - 34.




                                                                29
                                  bicubic                                            LDM-BSR




Figure 19. LDM-BSR generalizes to arbitrary inputs and can be used as a general-purpose upsampler, upscaling samples from the LSUN-
Cows dataset to 10242 resolution.



                                                                30
            input                GT             Pixel Baseline #1        Pixel Baseline #2   LDM #1            LDM #2




Figure 20. Qualitative superresolution comparison of two random samples between LDM-SR and baseline-diffusionmodel in Pixelspace.
Evaluated on imagenet validation-set after same amount of training steps.
                                                                    31
             input                 GT                LaMa [88]             LDM #1              LDM #2               LDM #3




Figure 21. Qualitative results on image inpainting. In contrast to [88], our generative approach enables generation of multiple diverse
samples for a given input.
                                                                  32
input                  result                              input               result




        Figure 22. More qualitative results on object removal as in Fig. 11.
                                        33
                    Semantic Synthesis on Flickr-Landscapes [23] (5122 finetuning)




Figure 23. Convolutional samples from the semantic landscapes model as in Sec. 4.3.2, finetuned on 5122 images.




                                                      34
Figure 24. A LDM trained on 2562 resolution can generalize to larger resolution for spatially conditioned tasks such as semantic synthesis
of landscape images. See Sec. 4.3.2.




                                                                   35
                                          Semantic Synthesis on Flickr-Landscapes [23]




Figure 25. When provided a semantic map as conditioning, our LDMs generalize to substantially larger resolutions than those seen during
training. Although this model was trained on inputs of size 2562 it can be used to create high-resolution samples as the ones shown here,
which are of resolution 1024 × 384.                                 36
                                 Random class conditional samples on the ImageNet dataset




Figure 26. Random samples from LDM-4 trained on the ImageNet dataset. Sampled with classifier-free guidance [32] scale s = 5.0 and
200 DDIM steps with η = 1.0.

                                                               37
                                 Random class conditional samples on the ImageNet dataset




Figure 27. Random samples from LDM-4 trained on the ImageNet dataset. Sampled with classifier-free guidance [32] scale s = 3.0 and
200 DDIM steps with η = 1.0.

                                                               38
                                       Random samples on the CelebA-HQ dataset




Figure 28. Random samples of our best performing model LDM-4 on the CelebA-HQ dataset. Sampled with 500 DDIM steps and η = 0
(FID = 5.15).




                                                            39
                                          Random samples on the FFHQ dataset




Figure 29. Random samples of our best performing model LDM-4 on the FFHQ dataset. Sampled with 200 DDIM steps and η = 1 (FID
= 4.98).




                                                            40
                                    Random samples on the LSUN-Churches dataset




Figure 30. Random samples of our best performing model LDM-8 on the LSUN-Churches dataset. Sampled with 200 DDIM steps and
η = 0 (FID = 4.48).




                                                           41
                                    Random samples on the LSUN-Bedrooms dataset




Figure 31. Random samples of our best performing model LDM-4 on the LSUN-Bedrooms dataset. Sampled with 200 DDIM steps and
η = 1 (FID = 2.95).




                                                           42
                                        Nearest Neighbors on the CelebA-HQ dataset




Figure 32. Nearest neighbors of our best CelebA-HQ model, computed in the feature space of a VGG-16 [79]. The leftmost sample is
from our model. The remaining samples in each row are its 10 nearest neighbors.




                                                              43
                                            Nearest Neighbors on the FFHQ dataset




Figure 33. Nearest neighbors of our best FFHQ model, computed in the feature space of a VGG-16 [79]. The leftmost sample is from our
model. The remaining samples in each row are its 10 nearest neighbors.




                                                                44
                                      Nearest Neighbors on the LSUN-Churches dataset




Figure 34. Nearest neighbors of our best LSUN-Churches model, computed in the feature space of a VGG-16 [79]. The leftmost sample
is from our model. The remaining samples in each row are its 10 nearest neighbors.




                                                               45
