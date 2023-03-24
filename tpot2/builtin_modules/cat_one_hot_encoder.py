import numpy as np
from scipy import sparse

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils import check_array
from sklearn.preprocessing import OneHotEncoder
import sklearn

import pandas as pd
from pandas.api.types import is_numeric_dtype



def auto_select_categorical_features(X):

    if not isinstance(X, pd.DataFrame):
        return []
    
    feature_mask = []
    for column in X.columns:
        feature_mask.append(not is_numeric_dtype(X[column]))

    return feature_mask


def _X_selected(X, selected):
    """Split X into selected features and other features"""
    X_sel = X[X.columns[selected]]
    X_not_sel = X.drop(X.columns[selected], axis=1)
    return X_sel, X_not_sel



class CatOneHotEncoder(BaseEstimator, TransformerMixin):


    def __init__(self, categorical_features='auto'):
        self.categorical_features = categorical_features


    def fit(self, X, y=None):
        """Fit OneHotEncoder to X, then transform X.

        Equivalent to self.fit(X).transform(X), but more convenient and more
        efficient. See fit for the parameters, transform for the return value.

        Parameters
        ----------
        X : array-like or sparse matrix, shape=(n_samples, n_features)
            Dense array or sparse matrix.
        y: array-like {n_samples,} (Optional, ignored)
            Feature labels
        """
        
        if self.categorical_features == "auto":
            self.categorical_features_ = auto_select_categorical_features(X)

        if sum(self.categorical_features_) == 0:
            return self
        
        self.enc = sklearn.preprocessing.OneHotEncoder(categories='auto', handle_unknown='ignore',sparse_output=False)

        #TODO make this more consistent with sklearn baseimputer/baseencoder
        if isinstance(X, pd.DataFrame):
            for col in X.columns:
                # check if the column name is not a string
                if not isinstance(col, str):
                    # if it's not a string, rename the column with "X" prefix
                    X.rename(columns={col: f"X{col}"}, inplace=True)


        if sum(self.categorical_features_) == X.shape[1]:
            X_sel = self.enc.fit(X)
        else:
            X_sel, X_not_sel = _X_selected(X, self.categorical_features_)
            X_sel = self.enc.fit(X_sel)
        
        return self
  
    def transform(self, X):
        """Transform X using one-hot encoding.

        Parameters
        ----------
        X : array-like or sparse matrix, shape=(n_samples, n_features)
            Dense array or sparse matrix.

        Returns
        -------
        X_out : sparse matrix if sparse=True else a 2-d array, dtype=int
            Transformed input.
        """

    
        if sum(self.categorical_features_) == 0:
            return X
        
        #TODO make this more consistent with sklearn baseimputer/baseencoder
        if isinstance(X, pd.DataFrame):
            for col in X.columns:
                # check if the column name is not a string
                if not isinstance(col, str):
                    # if it's not a string, rename the column with "X" prefix
                    X.rename(columns={col: f"X{col}"}, inplace=True)

        if sum(self.categorical_features_) == X.shape[1]:
            return self.enc.transform(X)
        else:

            X_sel, X_not_sel= _X_selected(X, self.categorical_features_)
            X_sel = self.enc.transform(X_sel)
            
            #If X is dataframe
            if isinstance(X, pd.DataFrame):
            
                X_sel = pd.DataFrame(X_sel, columns=self.enc.get_feature_names_out())
                return pd.concat([X_not_sel.reset_index(drop=True), X_sel.reset_index(drop=True)], axis=1)
            else:
                return np.hstack((X_not_sel, X_sel))
