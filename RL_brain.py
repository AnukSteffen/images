"""
The double DQN based on this paper: https://arxiv.org/abs/1509.06461

Converted from TensorFlow to PyTorch 2.5.1
Using: PyTorch 2.5.1, Python 3.9.25
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

np.random.seed(1)
torch.manual_seed(1)
if torch.cuda.is_available():
    torch.cuda.manual_seed(1)


class QNetwork(nn.Module):
    def __init__(self, n_features, n_actions):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(n_features, 20)
        self.fc2 = nn.Linear(20, n_actions)
        
        # Initialize weights
        nn.init.normal_(self.fc1.weight, 0, 0.003)
        nn.init.constant_(self.fc1.bias, 0.001)
        nn.init.normal_(self.fc2.weight, 0, 0.003)
        nn.init.constant_(self.fc2.bias, 0.001)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class DoubleDQN:
    def __init__(
            self,
            n_actions,
            n_features,
            learning_rate=0.005,
            reward_decay=0.9,
            e_greedy=0.9,
            replace_target_iter=200,
            memory_size=3200,
            batch_size=32,
            e_greedy_increment=None,
            output_graph=True,
            double_q=True,
            ris=True,
            passive_shift=True,
    ):
        self.n_actions = n_actions
        self.n_features = n_features
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon_max = e_greedy
        self.replace_target_iter = replace_target_iter
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.epsilon_increment = e_greedy_increment
        self.epsilon = 0 if e_greedy_increment is not None else self.epsilon_max

        self.double_q = double_q
        self.ris = ris
        self.passive_shift = passive_shift

        self.learn_step_counter = 0
        self.memory = np.zeros((self.memory_size, n_features * 2 + 3 + 1 + 1 + 1))
        self.memory_counter = 0
        
        # Device setup
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Build networks
        self.eval_net = QNetwork(n_features, n_actions).to(self.device)
        self.target_net = QNetwork(n_features, n_actions).to(self.device)
        self.target_net.load_state_dict(self.eval_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.RMSprop(self.eval_net.parameters(), lr=self.lr)
        self.loss_fn = nn.MSELoss()
        
        self.cost_his = []
        self.q = []
        self.running_q = 0

    def store_transition(self, s, a, r, s_):
        transition = np.hstack((s, a, r, s_))
        index = self.memory_counter % self.memory_size
        self.memory[index, :] = transition
        self.memory_counter += 1

    def choose_action(self, observation):
        observation = observation[np.newaxis, :]
        observation_tensor = torch.FloatTensor(observation).to(self.device)
        
        with torch.no_grad():
            actions_value = self.eval_net(observation_tensor).cpu().numpy()
        
        action_index = np.argmax(actions_value)

        self.running_q = self.running_q * 0.99 + 0.01 * np.max(actions_value)
        self.q.append(self.running_q)

        if np.random.uniform() > self.epsilon:
            action_index = np.random.randint(0, self.n_actions)

        return action_index

    def learn(self):
        if self.learn_step_counter % self.replace_target_iter == 0:
            self.target_net.load_state_dict(self.eval_net.state_dict())

        if self.memory_counter > self.memory_size:
            sample_index = np.random.choice(self.memory_size, size=self.batch_size)
        else:
            sample_index = np.random.choice(self.memory_counter, size=self.batch_size)
        
        batch_memory = self.memory[sample_index, :]

        # 1. 全部转换为 PyTorch Tensor 并放在对应的 Device (CPU/GPU) 上，避免数据搬运报错
        s = torch.FloatTensor(batch_memory[:, :self.n_features]).to(self.device)
        a = torch.LongTensor(batch_memory[:, self.n_features]).to(self.device) # Action 必须是 LongTensor
        r = torch.FloatTensor(batch_memory[:, self.n_features + 5]).to(self.device)
        s_ = torch.FloatTensor(batch_memory[:, -self.n_features:]).to(self.device)

        # 2. 获取 Q 值
        q_eval = self.eval_net(s)
        with torch.no_grad():
            q_next = self.target_net(s_)
            q_eval_next = self.eval_net(s_)

        # 3. Double DQN 逻辑处理
        if self.double_q:
            max_act4next = torch.argmax(q_eval_next, dim=1)
            selected_q_next = q_next[torch.arange(self.batch_size), max_act4next]
        else:
            selected_q_next = torch.max(q_next, dim=1)[0]

        # 4. 计算 Target Q
        q_target = q_eval.clone() # 在 PyTorch 中，通过 clone 配合后续的 loss_fn 就可以截断梯度
        q_target[torch.arange(self.batch_size), a] = r + self.gamma * selected_q_next

        # 5. 计算 Loss 并反向传播
        loss = self.loss_fn(q_eval, q_target)
        self.cost_his.append(loss.item())

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.epsilon = self.epsilon + self.epsilon_increment if self.epsilon < self.epsilon_max else self.epsilon_max
        self.learn_step_counter += 1