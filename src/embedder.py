import torch
from imagebind.models.imagebind_model import imagebind_huge, ModalityType
from imagebind import data
from torchvision import transforms
import torchaudio
from pytorchvideo.data.clip_sampling import ConstantClipsPerVideoSampler
import logging
import torch.nn.functional as F

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = imagebind_huge(pretrained=True)
model.eval()
model.to(device)

SAMPLE_RATE = 16000
NUM_MEL_BINS = 128
TARGET_LENGTH = 204
AUDIO_MEAN = -4.268
AUDIO_STD = 9.138
DEFAULT_AUDIO_FRAME_SHIFT_MS = 10

audio_normalizer = transforms.Normalize(mean=[AUDIO_MEAN], std=[AUDIO_STD])

def embed_image(img):
    try:
        data_transform = transforms.Compose(
            [
                transforms.Resize(224, interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=(0.48145466, 0.4578275, 0.40821073),
                    std=(0.26862954, 0.26130258, 0.27577711),
                ),
            ]
        )
        image = data_transform(img).to(device)
        inputs = {
            ModalityType.VISION: image.unsqueeze(0)
        }
        with torch.no_grad():
            embeddings = model(inputs)

        image_vector = embeddings[ModalityType.VISION].squeeze(0)
        return image_vector
    except Exception as e:
        print(f"Error processing image bytes: {e}")
        return None

def embed_text(text):
    try:
        text = text[0:100]
        print(f"Embedding text: {text}")
        inputs = {
            ModalityType.TEXT: data.load_and_transform_text([text], device),
        }
        print(f"inputs: {inputs}")

        with torch.no_grad():
            embeddings = model(inputs)

        print(f"embeddings: {embeddings}")

        text_vector = embeddings[ModalityType.TEXT]
        print(f"text_vector: {type(text_vector)} {text_vector.shape} {text_vector}")
        return text_vector
    except Exception as e:
        print(f"Error processing text: {e}")
        return None

def waveform2melspec(waveform, sample_rate, num_mel_bins, target_length):
    """
    This is the CORRECT spectrogram conversion function, using
    the exact parameters from the ImageBind paper.
    """
    # Based on https://github.com/facebookresearch/ImageBind/blob/main/imagebind/data.py
    waveform -= waveform.mean()
    fbank = torchaudio.compliance.kaldi.fbank(
        waveform,
        htk_compat=True,
        sample_frequency=sample_rate,
        use_energy=False,
        window_type="hanning",
        num_mel_bins=num_mel_bins,
        dither=0.0,
        frame_length=25,
        frame_shift=DEFAULT_AUDIO_FRAME_SHIFT_MS,
    )
    # Convert to [mel_bins, num_frames] shape
    fbank = fbank.transpose(0, 1)

    # Pad or Truncate the *spectrogram* to the target length
    n_frames = fbank.size(1)
    p = target_length - n_frames
    if p > 0:
        fbank = F.pad(fbank, (0, p), mode="constant", value=0)
    elif p < 0:
        fbank = fbank[:, 0:target_length]
    
    # Add a channel dimension: [1, mel_bins, num_frames]
    return fbank.unsqueeze(0)


def embed_audio(audio_bytes):
    """
    The main embedding function.
    Replaces your embed_audio and load_and_transform_audio_bytes.
    """
    try:
        # 1. Load bytes
        waveform, sr = torchaudio.load(audio_bytes)

        # 2. Resample
        if sr != SAMPLE_RATE:
            waveform = torchaudio.functional.resample(
                waveform, orig_freq=sr, new_freq=SAMPLE_RATE
            )
        
        # 3. Get mono
        waveform = waveform[0:1, :] # Shape [1, num_samples]

        # 4. Create spectrogram with the correct shape
        melspec = waveform2melspec(
            waveform, 
            SAMPLE_RATE, 
            NUM_MEL_BINS, 
            TARGET_LENGTH
        )
        # melspec shape is [1, 128, 204]
        
        # 5. Normalize
        melspec = audio_normalizer(melspec)
        
        # 6. Add batch dim and send to device
        # Final shape: [1, 1, 128, 204]
        audio_tensor = melspec.unsqueeze(0).to(device) 

        # 7. Prepare inputs
        inputs = {
            ModalityType.AUDIO: audio_tensor
        }

        # 8. Get embedding
        with torch.no_grad():
            embeddings = model(inputs)

        audio_vector = embeddings[ModalityType.AUDIO].squeeze(0)
        return audio_vector
    
    except Exception as e:
        print(f"Error processing audio bytes: {e}")
        return None
    
def load_and_transform_audio_bytes(
    audio_bytes,
    num_mel_bins=128,
    target_length=204,
    sample_rate=16000,
    clip_duration=2,
    clips_per_video=3,
    mean=-4.268,
    std=9.138,
):
    audio_outputs = []
    clip_sampler = ConstantClipsPerVideoSampler(
        clip_duration=clip_duration, clips_per_video=clips_per_video
    )

    waveform, sr = torchaudio.load(audio_bytes)
    if sample_rate != sr:
        waveform = torchaudio.functional.resample(
            waveform, orig_freq=sr, new_freq=sample_rate
        )
    all_clips_timepoints = get_clip_timepoints(
        clip_sampler, waveform.size(1) / sample_rate
    )
    all_clips = []
    for clip_timepoints in all_clips_timepoints:
        waveform_clip = waveform[
            :,
            int(clip_timepoints[0] * sample_rate) : int(
                clip_timepoints[1] * sample_rate
            ),
        ]
        waveform_melspec = waveform2melspec(
            waveform_clip, sample_rate, num_mel_bins, target_length
        )
        all_clips.append(waveform_melspec)

    normalize = transforms.Normalize(mean=mean, std=std)
    all_clips = [normalize(ac).to(device) for ac in all_clips]

    all_clips = torch.stack(all_clips, dim=0)
    audio_outputs.append(all_clips)

    return torch.stack(audio_outputs, dim=0)

def get_clip_timepoints(clip_sampler, duration):
    # Read out all clips in this video
    all_clips_timepoints = []
    is_last_clip = False
    end = 0.0
    while not is_last_clip:
        start, end, _, _, is_last_clip = clip_sampler(end, duration, annotation=None)
        all_clips_timepoints.append((start, end))
    return all_clips_timepoints

def waveform2melspec(waveform, sample_rate, num_mel_bins, target_length):
    # Based on https://github.com/YuanGongND/ast/blob/d7d8b4b8e06cdaeb6c843cdb38794c1c7692234c/src/dataloader.py#L102
    waveform -= waveform.mean()
    fbank = torchaudio.compliance.kaldi.fbank(
        waveform,
        htk_compat=True,
        sample_frequency=sample_rate,
        use_energy=False,
        window_type="hanning",
        num_mel_bins=num_mel_bins,
        dither=0.0,
        frame_length=25,
        frame_shift=DEFAULT_AUDIO_FRAME_SHIFT_MS,
    )
    # Convert to [mel_bins, num_frames] shape
    fbank = fbank.transpose(0, 1)
    # Pad to target_length
    n_frames = fbank.size(1)
    p = target_length - n_frames
    # if p is too large (say >20%), flash a warning
    if abs(p) / n_frames > 0.2:
        logging.warning(
            "Large gap between audio n_frames(%d) and "
            "target_length (%d). Is the audio_target_length "
            "setting correct?",
            n_frames,
            target_length,
        )
    # cut and pad
    if p > 0:
        fbank = torch.nn.functional.pad(fbank, (0, p), mode="constant", value=0)
    elif p < 0:
        fbank = fbank[:, 0:target_length]
    # Convert to [1, mel_bins, num_frames] shape, essentially like a 1
    # channel image
    fbank = fbank.unsqueeze(0)
    return fbank