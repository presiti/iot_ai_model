import torch
import torch.nn as nn

import numpy as np
from torch.utils.data import DataLoader 
import time
from tqdm import tqdm
import logging
import os
import torchmetrics

from dataset import CurrentDataset
from model import LSTMModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if __name__ == '__main__':
    labels = ['normal', 'def_baring', 'rotating_unbalance', 'def_shaft_alignment', 'loose_belt']
    model_path = "check_points/lstm/model_state_dict_best.pt"
    num_classes = len(labels)
    use_cpu = False
    
    device = torch.device("cuda" if (use_cpu) and torch.cuda.is_available() else "cpu")
    model = LSTMModel().to(device)
    model.load_state_dict(torch.load(model_path))
    model.eval()

    path = 'dataset/current/test/**/*.csv'
    dataset = CurrentDataset(path)
    total = len(dataset)
    dataloader = DataLoader(dataset,
                            batch_size=1,
                            shuffle=False,
                            pin_memory=True,
                            drop_last=False)
    
    preds = torch.tensor([],dtype= torch.int16).to(device)
    targets = torch.tensor([],dtype= torch.int16).to(device)

    
    criterion = nn.CrossEntropyLoss()
    f1socre = torchmetrics.F1Score(num_classes = num_classes)
    cm = torchmetrics.ConfusionMatrix(num_classes = num_classes)
    
    avg_cost = .0
    cnt = 0
    start_time = time.time()
    with torch.no_grad():
        # progress = tqdm(dataloader)
        for samples in dataloader:
            cnt+=1
            file_path, x_train, y_train = samples

            x_train = x_train.to(device)
            y_train = y_train.to(device)

            # H(x) 계산
            outputs = model(x_train)
            loss = criterion(outputs, y_train)  
            avg_cost += loss

            out = torch.max(outputs.data, 1)[1]
            y = torch.max(y_train.data, 1)[1]

            preds = torch.cat([preds, out])
            targets = torch.cat([targets, y])
            
            logger.info('{}/{} - {}, Predicted : {}, Actual : {}, Correct : {}, loss : {:.4f}'.format(cnt, total, file_path[0], labels[out[0]], labels[y[0]], out[0] == y[0], loss))
    
    f1 = f1socre(preds.to('cpu'), targets.to('cpu'))
    avg_cost = avg_cost / total
    
    logger.info('time : {:.2f}, loss : {:.4f}, f1-score : {:.4f}'.format(
            time.time()-start_time,
            avg_cost,
            f1
        )
    )