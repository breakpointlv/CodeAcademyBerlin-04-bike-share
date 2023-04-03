import torch
from numpy import ravel
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.metrics import mean_squared_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.utils import column_or_1d
from torch.autograd import Variable
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from torch.optim import Adam, LBFGS, SGD
from sklearn.preprocessing import StandardScaler, MinMaxScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge, BayesianRidge


class BikeRegression:

    ds = None
    input_features = []
    output_features = []
    X_train = None
    X_test = None
    y_train = None
    y_test = None
    X = None
    y = None

    def __init__(self, path_to_csv, input_features, output_features):

        self.input_features = input_features
        self.output_features = output_features

        self.ds = pd.read_csv(path_to_csv)

        # remove all data before 2017
        self.ds = self.ds[self.ds['year'] < 2017]

        self.ds['weekday_nr'] = self.ds['weekday'].map({
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6,
            'Sunday': 7
        })

        # drop na values for input and output features
        for feature in self.input_features:
            self.ds = self.ds[self.ds[feature].notna()]
        for feature in self.output_features:
            self.ds = self.ds[self.ds[feature].notna()]

        self.X = self.ds[self.input_features]
        self.y = self.ds[self.output_features]


    def split(self, test_size=0.8, random_state=42):
        from sklearn.model_selection import train_test_split
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            random_state=random_state
        )
        self.y_train = self.y_train.reshape(-1)
        self.y_test = self.y_test.reshape(-1)

    def scale(self):
        #scaler = StandardScaler()
        scaler = MinMaxScaler()
        self.X_train = pd.DataFrame(scaler.fit_transform(self.X_train), columns=self.X_train.columns)
        self.X_test = pd.DataFrame(scaler.transform(self.X_test), columns=self.X_test.columns)

    def plot(self):

        fig, axs = plt.subplots(nrows=len(self.input_features), ncols=1, figsize=(20, 40))
        ax_i = 0

        if len(self.input_features) == 1:
            axs = [axs]

        predict_y = self.predict(self.X_test).reshape(-1)
        for feature in self.input_features:
            plot_x = self.X_test[feature]
            plot_y = self.y_test.values.reshape(-1)
            sns.scatterplot(x=plot_x, y=plot_y, ax=axs[ax_i])

            plot_x = self.X_test[feature]
            plot_y = predict_y
            sns.lineplot(x=plot_x, y=plot_y, ax=axs[ax_i], color='red')

            ax_i += 1



class NNBikeRegression(BikeRegression):

    model = None
    optimizer = None
    loss_fn = None

    def __init__(self, path_to_csv, input_features, output_features):
        super().__init__(path_to_csv, input_features, output_features)

        # define the model, optimizer and loss function
        n_inputs = len(self.input_features)
        n_outputs = len(self.output_features)
        # self.model = torch.nn.Sequential(
        #     torch.nn.Linear(n_inputs, 10),
        #     torch.nn.ReLU(),
        #     torch.nn.Linear(10, 5),
        #     torch.nn.ReLU(),
        #     torch.nn.Linear(5, n_outputs)
        # )
        self.model = torch.nn.Linear(n_inputs, n_outputs)
        self.optimizer = LBFGS(self.model.parameters(), history_size=100, max_iter=100)
        self.loss_fn = torch.nn.MSELoss()

    def train(self, epochs):
        x_train = torch.tensor(self.X_train.values, dtype=torch.float32)
        y_train = torch.tensor(self.y_train.values, dtype=torch.float32)

        for epoch in range(epochs):
            running_loss = 0.0

            x_ = Variable(x_train, requires_grad=True)
            y_ = Variable(y_train)

            def closure():
                # Zero gradients
                self.optimizer.zero_grad()

                # Forward pass
                y_pred = self.model(x_)

                # Compute loss
                loss = self.loss_fn(y_pred, y_)

                # Backward pass
                loss.backward()

                return loss

            # Update weights
            self.optimizer.step(closure)

            # Update the running loss
            loss = closure()
            running_loss += loss.item()

            print(f"Epoch: {epoch + 1:02}/{epochs} Loss: {running_loss:.10f}")

    def predict(self, x):
        x = torch.tensor(x.values, dtype=torch.float32)
        return self.model(x).detach().numpy()

    def evaluate(self):
        x_test = torch.tensor(self.X_test.values, dtype=torch.float32)
        y_test = torch.tensor(self.y_test.values, dtype=torch.float32)
        y_pred = self.model(x_test).detach().numpy()
        loss = self.loss_fn(torch.tensor(y_pred, dtype=torch.float32), y_test).item()
        print(f"Loss: {loss:.10f}")



class SKBikeRegression(BikeRegression):

    model = None
    algo = None
    poly_degree = None

    algos = {
        'LinearRegression': LinearRegression,
        'Ridge': Ridge,
        'BayesianRidge': BayesianRidge,
        'Lasso': linear_model.Lasso,
        'ElasticNet': linear_model.ElasticNet,
        'DecisionTreeRegressor': DecisionTreeRegressor,
        'RandomForestRegressor': RandomForestRegressor,
        'GradientBoostingRegressor': GradientBoostingRegressor,
        'SVR': SVR,
        'KNeighborsRegressor': KNeighborsRegressor,
        'MLPRegressor': MLPRegressor,
    }
    chosen_algo = None

    def __init__(self, path_to_csv, input_features, output_features, algo, poly_degree=1):
        super().__init__(path_to_csv, input_features, output_features)
        self.algo = algo
        self.poly_degree = poly_degree

    def train(self):

        chosen_algo = self.algos[self.algo]

        if self.poly_degree > 1:
            poly = PolynomialFeatures(degree=self.poly_degree)
            self.X_train = poly.fit_transform(self.X_train)
            self.X_test = poly.transform(self.X_test)

        self.model = chosen_algo()

        self.model.fit(self.X_train, self.y_train)

    def predict(self, x):
        return self.model.predict(x)

    def evaluate(self):
        return mean_squared_error(self.y_test, self.predict(self.X_test))
