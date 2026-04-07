import torch
import torch.nn as nn

class EEGNetFeatureExtractor(nn.Module):
    """
    Standard EEGNetv4 feature extractor modified to output contextual embeddings 
    for the Transformer backbone instead of direct classification.
    """
    def __init__(self, num_channels=18, num_samples=2400, F1=8, D=2, F2=16, kernel_length=64, drop_rate=0.25):
        super(EEGNetFeatureExtractor, self).__init__()
        
        # Block 1 - Spatial and Temporal Convolutions
        self.conv1 = nn.Conv2d(1, F1, (1, kernel_length), padding='same', bias=False)
        self.batchnorm1 = nn.BatchNorm2d(F1)
        
        # Depthwise Spatial Convolution (over channels)
        self.depthwise = nn.Conv2d(F1, F1 * D, (num_channels, 1), groups=F1, bias=False)
        self.batchnorm2 = nn.BatchNorm2d(F1 * D)
        self.activation1 = nn.ELU()
        
        self.avgpool1 = nn.AvgPool2d((1, 4))
        self.dropout1 = nn.Dropout(p=drop_rate)
        
        # Block 2 - Separable Convolution
        self.separable = nn.Conv2d(F1 * D, F2, (1, 16), padding='same', groups=F1 * D, bias=False)
        self.pointwise = nn.Conv2d(F2, F2, (1, 1), bias=False)
        self.batchnorm3 = nn.BatchNorm2d(F2)
        
        self.activation2 = nn.ELU()
        self.avgpool2 = nn.AvgPool2d((1, 8))
        self.dropout2 = nn.Dropout(p=drop_rate)
        
        self.out_len = num_samples // 32
        self.out_features = F2
        
    def forward(self, x):
        # x is (Batch, Channels, Time) -> EEGNet expects (B, 1, Channels, Time)
        x = x.unsqueeze(1)
        
        # Temporal Convolution
        x = self.conv1(x)
        x = self.batchnorm1(x)
        
        # Spatial Depthwise Convolution
        x = self.depthwise(x)
        x = self.batchnorm2(x)
        x = self.activation1(x)
        x = self.avgpool1(x)
        x = self.dropout1(x)
        
        # Separable Convolution
        x = self.separable(x)
        x = self.pointwise(x)
        x = self.batchnorm3(x)
        x = self.activation2(x)
        x = self.avgpool2(x)
        x = self.dropout2(x)
        
        # Shape out is (B, F2, 1, out_len) -> strip height dim
        x = x.squeeze(2)
        # Returns (B, Features, Time_Steps)
        return x


class BIOTEncoder(nn.Module):
    """
    Simplified BIOT Backbone: 
    Transformer Encoder operating on contextualized EEG embeddings over time.
    """
    def __init__(self, embed_dim=16, num_heads=4, depth=2, dropout=0.2):
        super(BIOTEncoder, self).__init__()
        
        self.project_in = nn.Conv1d(16, embed_dim, kernel_size=1)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, 
            nhead=num_heads, 
            dim_feedforward=embed_dim*4, 
            dropout=dropout, 
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=depth)

    def forward(self, x):
        # x shape: (B, F2, Time_Steps)
        x = self.project_in(x)
        
        # Transformer Batch First expects (Batch, Sequence, Features)
        x = x.permute(0, 2, 1)
        
        encoded = self.transformer(x)
        return encoded


class EpiChatModel(nn.Module):
    """
    EpiChat Hybrid Multi-class Model:
    Inputs -> (EEGNetv4 Extractor) -> (BIOT Transformer) -> (Classification Head)
    Outputs Probabilities of Background (0) vs Seizure (1)
    """
    def __init__(self, num_channels=18, num_samples=2400, num_classes=2):
        super(EpiChatModel, self).__init__()
        
        # 1. Feature Extraction backbone
        self.eegnet = EEGNetFeatureExtractor(
            num_channels=num_channels, 
            num_samples=num_samples,
            F1=8, D=2, F2=16, drop_rate=0.25
        )
        
        # 2. Sequence Modeling via BIOT Transformers
        self.biot = BIOTEncoder(
            embed_dim=16,
            num_heads=4,
            depth=2,
            dropout=0.25
        )
        
        # Calculate Flatten space 
        self.seq_len = num_samples // 32
        self.flatten_dim = self.seq_len * 16
        
        # 3. Dense Classifier Head
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self.flatten_dim, 128),
            nn.ELU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
        
    def forward(self, x):
        features = self.eegnet(x)
        encoded = self.biot(features)
        out = self.classifier(encoded)
        return out
