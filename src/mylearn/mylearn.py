import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.datasets import fetch_california_housing, load_iris
from sklearn.linear_model import LinearRegression, LogisticRegression, Lasso, Ridge
from sklearn.svm import LinearSVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import r2_score, confusion_matrix
from sklearn.inspection import permutation_importance
#
class MyLearn:
    def __init__(self, pddataframe):
        #self.model = Ridge(alpha=0.1)
        self.model = LinearRegression()
        #self.model = LogisticRegression()
        self.dataset = fetch_california_housing()   # テスト用データセット
        self.column_names = None
        self.mdf = None
        self.data = None
        self.target = None
        self.d_train = None
        self.t_train = None
        self.d_test = None
        self.t_test = None
        self.t_pred_test = None
        #
        pdf = pddataframe
        
        pdf['histgram'] = pdf['macd'] - pdf['signal'] 
        pdf['volatility'] = (pdf['High'] - pdf['Low']) / pdf['Close']
        #pdf['close_off_high'] = (pdf['High'] - pdf['Close']) / (pdf['High'] - pdf['Low'])
        
        self.mdf = pdf
        #print(self.mdf.columns)
    #
    def set_model(self, model):
        self.model = model
        return
    #
    def tarin_test_split(self, size = 0.5):
        
        '''
        self.data = self.dataset.data
        self.target = self.dataset.target
        self.column_names = self.dataset.feature_names
        '''
        self.target = self.mdf['Close'].shift(-1).fillna(method='ffill').to_numpy(copy=True)
        drop_columns = ['Open','High','Low','std','volatility','histgram','ema12','ema26','signal','macd']
        self.mdf = self.mdf.drop( drop_columns, axis=1)
        self.column_names = self.mdf.columns
        self.data = self.mdf.to_numpy()        
        #
        self.d_train, self.d_test, self.t_train, self.t_test = train_test_split(self.data, self.target, test_size=size, random_state=0)
        print(f"test_size = {size} train-data count: {len(self.d_train)}")
        print(pd.DataFrame(self.d_train, columns=self.column_names).tail())
        print(pd.DataFrame(self.t_train, columns=['target']).tail())
        return
    #
    def execute(self):
        #
        self.model.fit(self.d_train, self.t_train)
        #
        self.t_pred_test = self.model.predict(self.d_test)
        print(f"test :\n {self.t_test}")        
        return self.t_pred_test
    #
    def show_explanation(self):
        #
        print(f'R2 score: {r2_score(self.t_test, self.t_pred_test):.4f}')
        #
        rslt = permutation_importance(self.model, self.d_test, self.t_test, n_repeats=10, random_state=42, n_jobs=2) 
        for i in rslt.importances_mean.argsort()[::-1]:
            if rslt.importances_mean[i] - 2 * rslt.importances_std[i] > 0:
                print(f"[{i:>2}] {self.column_names[i]:<10}: "
                      f"{rslt.importances_mean[i]:5.3f}"
                      f" +/- {rslt.importances_std[i]:5.3f}")
        return rslt
    

