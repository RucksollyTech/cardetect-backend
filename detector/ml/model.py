import torch
import torchvision.models as models
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import json
from django.conf import settings

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

def get_model():
    global _model, _class_names
    if _model is None:
        checkpoint = torch.load(settings.ML_MODEL_PATH, map_location='cpu',weights_only=False)
        _class_names = checkpoint['class_names']
        _model = _build_model()
        _model.load_state_dict(checkpoint['model_state_dict'])
        _model.eval()
    return _model, _class_names

def predict(image_file, top_k=5):
    model, class_names = get_model()
    img = Image.open(image_file).convert('RGB')
    tensor = val_transform(img).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
    probs = torch.softmax(logits, dim=1)
    top = torch.topk(probs, top_k)
    return [
        {'class': class_names[i], 'confidence': round(p * 100, 2)}
        for i, p in zip(top.indices[0].tolist(), top.values[0].tolist())
    ]