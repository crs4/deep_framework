import torchvision
resnet = torchvision.models.resnet.__dict__["resnet50"](pretrained=True)