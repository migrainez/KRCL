import torch
import torch.nn.functional as F

class Contrast(torch.nn.Module):
    def __init__(self, num_hidden: int, tau: float = 0.7):
        super(Contrast, self).__init__()
        self.tau: float = tau

        self.mlp1 = torch.nn.Sequential(
            torch.nn.Linear(num_hidden, num_hidden, bias=True),
            torch.nn.ReLU(),
            torch.nn.Linear(num_hidden, num_hidden, bias=True),
        )
        self.mlp2 = torch.nn.Sequential(
            torch.nn.Linear(num_hidden, num_hidden, bias=True),
            torch.nn.ReLU(),
            torch.nn.Linear(num_hidden, num_hidden, bias=True),
        )

    def sim(self, z1: torch.Tensor, z2: torch.Tensor):
        z1 = F.normalize(z1)
        z2 = F.normalize(z2)
        return torch.mm(z1, z2.t())
    
    def self_sim(self, z1, z2):
        z1 = F.normalize(z1)
        z2 = F.normalize(z2)
        return (z1 * z2).sum(1)

    def loss(self, z1: torch.Tensor, z2: torch.Tensor):
        f = lambda x: torch.exp(x / self.tau)
        between_sim = f(self.self_sim(z1, z2))
        rand_item = torch.randperm(z1.shape[0])
        neg_sim = f(self.self_sim(z1, z2[rand_item])) + f(self.self_sim(z2, z1[rand_item]))

        return -torch.log(between_sim / (between_sim + between_sim + neg_sim))

    def forward(self, z1: torch.Tensor, z2: torch.Tensor):
        h1 = self.mlp1(z1)
        h2 = self.mlp1(z2)
        loss = self.loss(h1, h2).mean()
        return loss



def InfoNCE(view1, view2, temperature: float, b_cos: bool = True):
    """
    Args:
        view1: (torch.Tensor - N x D)
        view2: (torch.Tensor - N x D)
        temperature: float
        b_cos (bool)

    Return: Average InfoNCE Loss
    """
    if b_cos:
        view1, view2 = F.normalize(view1, dim=1), F.normalize(view2, dim=1)

    pos_score = (view1 @ view2.T) / temperature
    score = torch.diag(F.log_softmax(pos_score, dim=1))
    return -score.mean()


