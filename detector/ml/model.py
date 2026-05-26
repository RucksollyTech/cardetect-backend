import torch
import torchvision.models as models
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import json
from django.conf import settings
from huggingface_hub import hf_hub_download
import os
torch.set_num_threads(1)

IMG_SIZE = 384

val_transform = transforms.Compose([
    transforms.Resize(440),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def _build_model(num_classes=196):
    model = models.resnet50(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.BatchNorm1d(in_features),
        nn.Dropout(0.4),
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.BatchNorm1d(512),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes)
    )
    return model

# Load once at startup, not per request
_model = None
_class_names = None

torch.set_num_threads(1)

def get_model():
    global _model, _class_names

    if _model is None:
        model_path = hf_hub_download(
            repo_id=settings.HF_REPO_ID,
            filename="cardetect_final.pt",
            cache_dir="/tmp/hf_cache"
        )

        checkpoint = torch.load(
            model_path,
            map_location="cpu",
            weights_only=False
        )

        _class_names = checkpoint["class_names"]

        model = _build_model()
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        _model = model

    return _model, _class_names


def predict(image_file, top_k=5):
    model, class_names = get_model()

    img = Image.open(image_file).convert("RGB")
    tensor = val_transform(img).unsqueeze(0)

    with torch.inference_mode():
        logits = model(tensor)

    probs = torch.softmax(logits, dim=1)
    top = torch.topk(probs, top_k)

    return [
        {
            "class": class_names[i],
            "confidence": round(p * 100, 2),
        }
        for i, p in zip(
            top.indices[0].tolist(),
            top.values[0].tolist()
        )
    ]