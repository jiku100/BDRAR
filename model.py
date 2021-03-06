import torch
import torch.nn.functional as F
from torch import nn

from resnext.resnext101_regular import ResNeXt101

class _AttentionModule(nn.Module):
    def __init__(self):
        super(_AttentionModule, self).__init__()
        self.block1 = nn.Sequential(
            nn.Conv2d(64, 64, 1, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, dilation=2, padding=2, groups=32, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 1, bias=False), nn.BatchNorm2d(64)
        )
        self.block2 = nn.Sequential(
            nn.Conv2d(64, 64, 1, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, dilation=3, padding=3, groups=32, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 1, bias=False), nn.BatchNorm2d(64)
        )
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 64, 1, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, dilation=4, padding=4, groups=32, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.down = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32)
        )

    def forward(self, x):
        out1 = nn.ReLU()(self.block1(x) + x)
        out2 = nn.ReLU()(self.block2(out1) + out1)
        out3 = nn.Sigmoid()(self.block3(out2) + self.down(out2))
        return out3

class BDRAR(nn.Module):
    def __init__(self):
        super(BDRAR, self).__init__()
        resnext = ResNeXt101()
        self.layer0 = resnext.layer0
        self.layer1 = resnext.layer1
        self.layer2 = resnext.layer2
        self.layer3 = resnext.layer3
        self.layer4 = resnext.layer4

        self.down4 = nn.Sequential(
            nn.Conv2d(2048, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU()
        )
        self.down3 = nn.Sequential(
            nn.Conv2d(1024, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU()
        )
        self.down2 = nn.Sequential(
            nn.Conv2d(512, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU()
        )
        self.down1 = nn.Sequential(
            nn.Conv2d(256, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU()
        )

        self.refine3_hl = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.refine2_hl = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.refine1_hl = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.attention3_hl = _AttentionModule()
        self.attention2_hl = _AttentionModule()
        self.attention1_hl = _AttentionModule()

        self.refine2_lh = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.refine4_lh = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.refine3_lh = nn.Sequential(
            nn.Conv2d(64, 32, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1, groups=32, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 1, bias=False), nn.BatchNorm2d(32)
        )
        self.attention2_lh = _AttentionModule()
        self.attention3_lh = _AttentionModule()
        self.attention4_lh = _AttentionModule()

        self.fuse_attention = nn.Sequential(
            nn.Conv2d(64, 16, 3, padding=1, bias=False), nn.BatchNorm2d(16), nn.ReLU(),
            nn.Conv2d(16, 2, 1)
        )

        self.predict = nn.Sequential(
            nn.Conv2d(32, 8, 3, padding=1, bias=False), nn.BatchNorm2d(8), nn.ReLU(),
            nn.Dropout(0.1), nn.Conv2d(8, 1, 1)
        )

    def forward(self, x):
        layer0 = self.layer0(x)
        layer1 = self.layer1(layer0)
        layer2 = self.layer2(layer1)
        layer3 = self.layer3(layer2)
        layer4 = self.layer4(layer3)

        down4 = self.down4(layer4)
        down3 = self.down3(layer3)
        down2 = self.down2(layer2)
        down1 = self.down1(layer1)

        down4_upsample = nn.Upsample(size=down3.size()[2:], mode='bilinear')(down4)
        refine3_hl_0 = self.refine3_hl(torch.cat((down4_upsample, down3), 1)) + down4_upsample
        refine3_hl_0_ReLU = nn.ReLU(inplace = True)(refine3_hl_0)
        refine3_hl_0_attention = (1 + self.attention3_hl(torch.cat((down4_upsample, down3), 1))) * refine3_hl_0_ReLU
        refine3_hl_1 = self.refine3_hl(torch.cat((refine3_hl_0_attention, down3), 1)) + refine3_hl_0_attention
        refine3_hl_1_ReLU = nn.ReLU(inplace = True)(refine3_hl_1)
        refine3_hl_1_attention = (1 + self.attention3_hl(torch.cat((refine3_hl_0_attention, down3), 1))) * refine3_hl_1_ReLU

        refine3_hl_1_upsample = nn.Upsample(size=down2.size()[2:], mode='bilinear')(refine3_hl_1_attention)
        refine2_hl_0 = self.refine2_hl(torch.cat((refine3_hl_1_upsample, down2), 1)) + refine3_hl_1_upsample
        refine2_hl_0_ReLU = nn.ReLU(inplace = True)(refine2_hl_0)
        refine2_hl_0_attention = (1 + self.attention2_hl(torch.cat((refine3_hl_1_upsample, down2), 1))) * refine2_hl_0_ReLU
        refine2_hl_1 = self.refine2_hl(torch.cat((refine2_hl_0_attention, down2), 1)) + refine2_hl_0_attention
        refine2_hl_1_ReLU = nn.ReLU(inplace = True)(refine2_hl_1)
        refine2_hl_1_attention = (1 + self.attention2_hl(torch.cat((refine2_hl_0_attention, down2), 1))) * refine2_hl_1_ReLU

        refine2_hl_1_upsample = nn.Upsample(size=down1.size()[2:], mode='bilinear')(refine2_hl_1_attention)
        refine1_hl_0 = self.refine1_hl(torch.cat((refine2_hl_1_upsample, down1), 1)) + refine2_hl_1_upsample
        refine1_hl_0_ReLU = nn.ReLU(inplace = True)(refine1_hl_0)
        refine1_hl_0_attention = (1 + self.attention1_hl(torch.cat((refine2_hl_1_upsample, down1), 1))) * refine1_hl_0_ReLU
        refine1_hl_1 = self.refine1_hl(torch.cat((refine1_hl_0_attention, down1), 1)) + refine1_hl_0_attention
        refine1_hl_1_ReLU = nn.ReLU(inplace = True)(refine1_hl_1)
        refine1_hl_1_attention = (1 + self.attention1_hl(torch.cat((refine1_hl_0_attention, down1), 1))) * refine1_hl_1_ReLU

        down2_upsample = nn.Upsample(size=down1.size()[2:], mode='bilinear')(down2)
        refine2_lh_0 = self.refine2_lh(torch.cat((down1, down2_upsample), 1)) + down1
        refine2_lh_0_ReLU = nn.ReLU(inplace = True)(refine2_lh_0)
        refine2_lh_0_attention = (1 + self.attention2_lh(torch.cat((down1, down2_upsample), 1))) * refine2_lh_0_ReLU
        refine2_lh_1 = self.refine2_lh(torch.cat((refine2_lh_0_attention, down2_upsample), 1)) + refine2_lh_0_attention
        refine2_lh_1_ReLU = nn.ReLU(inplace = True)(refine2_lh_1)
        refine2_lh_1_attention = (1 + self.attention2_lh(torch.cat((refine2_lh_0_attention, down2_upsample), 1))) * refine2_lh_1_ReLU

        down3_upsample = nn.Upsample(size=down1.size()[2:], mode='bilinear')(down3)
        refine3_lh_0 = self.refine3_lh(torch.cat((refine2_lh_1_attention, down3_upsample), 1)) + refine2_lh_1_attention
        refine3_lh_0_ReLU = nn.ReLU(inplace = True)(refine3_lh_0)
        refine3_lh_0_attention = (1 + self.attention3_lh(torch.cat((refine2_lh_1_attention, down3_upsample), 1))) * refine3_lh_0_ReLU
        refine3_lh_1 = self.refine3_lh(torch.cat((refine3_lh_0_attention, down3_upsample), 1)) + refine3_lh_0_attention
        refine3_lh_1_ReLU = nn.ReLU(inplace = True)(refine3_lh_1)
        refine3_lh_1_attention = (1 + self.attention3_lh(torch.cat((refine3_lh_0_attention, down3_upsample), 1))) * refine3_lh_1_ReLU

        down4_upsample = nn.Upsample(size=down1.size()[2:], mode='bilinear')(down4)
        refine4_lh_0 = self.refine4_lh(torch.cat((refine3_lh_1_attention, down4_upsample), 1)) + refine3_lh_1_attention
        refine4_lh_0_ReLU = nn.ReLU(inplace = True)(refine4_lh_0)
        refine4_lh_0_attention = (1 + self.attention4_lh(torch.cat((refine3_lh_1_attention, down4_upsample), 1))) * refine4_lh_0_ReLU
        refine4_lh_1 = self.refine4_lh(torch.cat((refine4_lh_0_attention, down4_upsample), 1)) + refine4_lh_0_attention
        refine4_lh_1_ReLU = nn.ReLU(inplace = True)(refine4_lh_1)
        refine4_lh_1_attention = (1 + self.attention4_lh(torch.cat((refine4_lh_0_attention, down4_upsample), 1))) * refine4_lh_1_ReLU

        refine3_hl_1_upsample = nn.Upsample(size=down1.size()[2:], mode='bilinear')(refine3_hl_1_attention)
        predict4_hl = self.predict(down4)
        predict3_hl = self.predict(refine3_hl_1_upsample)
        predict2_hl = self.predict(refine2_hl_1_upsample)
        predict1_hl = self.predict(refine1_hl_1_attention)

        predict1_lh = self.predict(down1)
        predict2_lh = self.predict(refine2_lh_1_attention)
        predict3_lh = self.predict(refine3_lh_1_attention)
        predict4_lh = self.predict(refine4_lh_1_attention)

        fuse_attention = nn.Sigmoid()(self.fuse_attention(torch.cat((refine1_hl_1_attention, refine4_lh_1_attention), 1)))
        fuse_predict = torch.sum(fuse_attention * torch.cat((predict1_hl, predict4_lh), 1), 1, True)

        predict4_hl_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict4_hl)
        predict3_hl_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict3_hl)
        predict2_hl_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict2_hl)
        predict1_hl_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict1_hl)
        predict1_lh_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict1_lh)
        predict2_lh_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict2_lh)
        predict3_lh_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict3_lh)
        predict4_lh_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(predict4_lh)
        fuse_predict_upsample = nn.Upsample(size=x.size()[2:], mode='bilinear')(fuse_predict)

        if self.training:
            return fuse_predict_upsample, predict1_hl_upsample, predict2_hl_upsample, predict3_hl_upsample, predict4_hl_upsample, predict1_lh_upsample, predict2_lh_upsample, predict3_lh_upsample, predict4_lh_upsample
        return nn.Sigmoid()(fuse_predict_upsample)