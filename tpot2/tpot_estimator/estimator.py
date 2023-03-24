from sklearn.base import BaseEstimator
from sklearn.utils.metaestimators import available_if
import numpy as np
import typing
import sklearn.metrics
import tpot2.estimator_objective_functions
from functools import partial
import tpot2.config
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.preprocessing import LabelEncoder 
from sklearn.utils.multiclass import unique_labels 
import pandas as pd
from sklearn.model_selection import train_test_split
import tpot2


EVOLVERS = {"nsga2":tpot2.evolutionary_algorithms.eaNSGA2.eaNSGA2_Evolver}



#TODO inherit from _BaseComposition?
class TPOTEstimator(BaseEstimator):
    def __init__(self, scorers, 
                        scorers_weights,
                        classification,
                        population_size = 100,
                        generations = 100,
                        initial_population_size = None,
                        population_scaling = .8, 
                        generations_until_end_population = 1,  
                        callback: tpot2.CallBackInterface = None,
                        n_jobs=1,
                        
                        cv = 5,
                        verbose = 0, #TODO
                        other_objective_functions=[tpot2.estimator_objective_functions.average_path_length_objective], #tpot2.estimator_objective_functions.complexity_objective],
                        other_objective_functions_weights = [-1],
                        bigger_is_better = True,
                        evolver = "nsga2",
                        evolver_params = {},
                        max_depth = np.inf,
                        max_size = np.inf, 
                        max_children = np.inf,
                        root_config_dict= 'Auto',
                        inner_config_dict=["selectors", "transformers"],
                        leaf_config_dict= None,

                        subsets = None,

                        max_time_seconds=float('inf'), 
                        max_eval_time_seconds=60*10, 
                        

                        n_initial_optimizations = 0,
                        optimization_cv = 3,
                        max_optimize_time_seconds=60*20,
                        optimization_steps = 10,

                        periodic_checkpoint_folder = None,

                        threshold_evaluation_early_stop = None, 
                        threshold_evaluation_scaling = 4,
                        min_history_threshold = 20,
                        selection_evaluation_early_stop = None, 
                        selection_evaluation_scaling = 4, 

                        scorers_early_stop_tol = 0.001,
                        other_objectives_early_stop_tol =None,
                        early_stop = None,

                        warm_start = False,
                        memory = None,
                        cross_val_predict_cv = 0,
                        
                        budget_range = None,
                        budget_scaling = .8,
                        generations_until_end_budget = 1,  


                        preprocessing = False,  

                        validation_strategy = "none",
                        validation_fraction = .2,

                        subset_column = None,

                        stepwise_steps = 5,
                        ):
                        
        '''
        An sklearn baseestimator that uses genetic programming to optimize a pipeline.
        
        Parameters:
        - population_size (int):    The size of the population. 
            The initial population will be randomly generated in this size. Each generation population_size individuals will be generated.
        
        - generations (int): The number of generations to evolve the population.
        
        initial_population_size : int
            Size of the initial population. If None, population_size will be used.

        - callback (tpot2.CallBackInterface): NOT YET IMPLEMENTED A callback function to be called after each generation.
        
        - n_jobs (int): Number of CPU cores to use during the optimization process. TODO: check, more jobs sometimes utitlizes more threads more efficiently
        
        - scorers (list, scorer): A scorer or list of scorers to be used in the cross-validation process. 
            see https://scikit-learn.org/stable/modules/model_evaluation.html
        
        - scorers_weights (list): A list of weights to be applied to the scorers during the optimization process.
        
        - cv (int): Number of folds to use in the cross-validation process.
        
        - verbose (int): How much information to print during the optimization process. Higher values include the information from lower values.
            0. nothing
            1. progress bar
            2. evaluations progress bar
            3. best individual
            4. warnings
            5. full warnings trace
        
        - other_objective_functions (list): A list of other objective functions to apply to the pipeline.
        
        - other_objective_functions_weights (list): A list of weights to be applied to the other objective functions.
        
        - bigger_is_better (bool): A flag indicating whether bigger score is better or smaller score is better. 
            Applies to the scores multiplied by the weights. 
            For instance, if bigger_is_better is True, and the weight is 1, then the optimizer will try to maximize the raw score.
            If bigger_is_better is True, and the weight is -1, then the optimizer will try to minimize the raw score.
            If bigger_is_better is False, and the weight is 1, then the optimizer will try to minimize the raw score.
            If bigger_is_better is False, and the weight is -1, then the optimizer will try to maximize the raw score.
        
        - evolver (tpot2.evolutionary_algorithms.eaNSGA2.eaNSGA2_Evolver): The evolver to use for the optimization process. See tpot2.evolutionary_algorithms
            - type : an type or subclass of a BaseEvolver
            - "nsga2" : tpot2.evolutionary_algorithms.eaNSGA2.eaNSGA2_Evolver
        
        - evolver_params (dict): A dictionary of parameters for the evolver.
        
        - max_depth (int): The maximum depth from any node to the root of the pipelines to be generated.
        
        - max_size (int): The maximum number of nodes of the pipelines to be generated.
        
        - max_children (int): The maximum number of children nodes in the pipelines can have. If set to 1, the pipelines will be linear.
        
        - root_config_dict (dict): The configuration dictionary to use for the root node of the model.
            Default 'auto'
            - 'selectors' : A selection of sklearn Selector methods.
            - 'classifiers' : A selection of sklearn Classifier methods.
            - 'regressors' : A selection of sklearn Regressor methods.
            - 'transformers' : A selection of sklearn Transformer methods.
            - 'arithmetic_transformer' : A selection of sklearn Arithmetic Transformer methods that replicate symbolic classification/regression operators.
            - 'passthrough' : A node that just passes though the input. Useful for passing through raw inputs into inner nodes.
            - 'feature_set_selector' : A selector that pulls out specific subsets of columns from the data. Only well defined as a leaf.
                                        Subsets are set with the subsets parameter.
            - list : a list of strings out of the above options to include the corresponding methods in the configuration dictionary.
        

        - inner_config_dict (dict): The configuration dictionary to use for the inner nodes of the model generation.
            Default ["selectors", "transformers"]
            - 'selectors' : A selection of sklearn Selector methods.
            - 'classifiers' : A selection of sklearn Classifier methods.
            - 'regressors' : A selection of sklearn Regressor methods.
            - 'transformers' : A selection of sklearn Transformer methods.
            - 'arithmetic_transformer' : A selection of sklearn Arithmetic Transformer methods that replicate symbolic classification/regression operators.
            - 'passthrough' : A node that just passes though the input. Useful for passing through raw inputs into inner nodes.
            - 'feature_set_selector' : A selector that pulls out specific subsets of columns from the data. Only well defined as a leaf.
                                        Subsets are set with the subsets parameter.
            - list : a list of strings out of the above options to include the corresponding methods in the configuration dictionary.

        - leaf_config_dict (dict): The configuration dictionary to use for the leaf node of the model. If set, leaf nodes must be from this dictionary.
            Otherwise leaf nodes will be generated from the root_config_dict. 
            Default None
            - 'selectors' : A selection of sklearn Selector methods.
            - 'classifiers' : A selection of sklearn Classifier methods.
            - 'regressors' : A selection of sklearn Regressor methods.
            - 'transformers' : A selection of sklearn Transformer methods.
            - 'arithmetic_transformer' : A selection of sklearn Arithmetic Transformer methods that replicate symbolic classification/regression operators.
            - 'passthrough' : A node that just passes though the input. Useful for passing through raw inputs into inner nodes.
            - 'feature_set_selector' : A selector that pulls out specific subsets of columns from the data. Only well defined as a leaf.
                                        Subsets are set with the subsets parameter.
            - list : a list of strings out of the above options to include the corresponding methods in the configuration dictionary.

        - subsets : Sets the subsets that the FeatureSetSeletor will select from if set as an option in one of the configuration dictionaries.
            Default None
            - str : If a string, it is assumed to be a path to a csv file with the subsets. 
                The first column is assumed to be the name of the subset and the remaining columns are the features in the subset.
            - list or np.ndarray : If a list or np.ndarray, it is assumed to be a list of subsets.
            - None : If None, each column will be treated as a subset. One column will be selected per subset.
            If subsets is None, each column will be treated as a subset. One column will be selected per subset.

        - max_time_seconds (float): The maximum time in seconds that the optimization process should run for. Will finish current generation and then stop.
       
        - max_eval_time_seconds (float): The maximum time in seconds that the evaluation of a model should take.
            If the evaluation takes longer than this, the model will be discarded.
            Set to None for no timer limit.
        
        - classification (bool): A flag indicating whether the problem is a classification problem or not.
        
        - n_initial_optimizations (int): NOT YET IMPLEMENTED Number of initial optimizations to perform.
            TODO Not implemented yet.
        
        - optimization_cv (int): NOT YET IMPLEMENTED  Number of folds to use for the optuna optimization's internal cross-validation.
        
        - max_optimize_time_seconds (int): NOT YET IMPLEMENTED The maximum time in seconds that the optuna internal optimization process should run for.
        
        - optimization_steps (int): NOT YET IMPLEMENTED Number of steps to take during the internal optimization process.
        
        - periodic_checkpoint_folder : str
            Folder to save the population to periodically. If None, no periodic saving will be done. Will save once every generation but not more than once every 10 minutes.
            If provided, training will resume from this checkpoint.

        - threshold_evaluation_early_stop (list): [start, end] EXPERIMENTAL A starting and ending percentile to use as a threshold for the evaluation early stopping.
            Values between 0 and 100.
        - threshold_evaluation_scaling (float): [0,inf) EXPERIMENTAL A scaling factor to use when determining how fast we move the threshold moves from the start to end percentile.
            Must be greater than zero. Higher numbers will move the threshold to the end faster.
        
        - min_history_threshold (int): EXPERIMENTAL The minimum number of previous scores needed before using threshold early stopping.
        
        - selection_evaluation_early_stop (list): EXPERIMENTAL A lower and upper percent of the population size to select each round of CV.
            Values between 0 and 1.
        
        - selection_evaluation_scaling (float): EXPERIMENTAL A scaling factor to use when determining how fast we move the threshold moves from the start to end percentile.
            Must be greater than zero. Higher numbers will move the threshold to the end faster.

        - scorers_early_stop_tol : 
            -list of floats
                list of tolerances for each scorer. If the difference between the best score and the current score is less than the tolerance, the individual is considered to have converged
                If an index of the list is None, that item will not be used for early stopping
            -int 
                If an int is given, it will be used as the tolerance for all objectives
        - other_objectives_early_stop_tol : 
            -list of floats
                list of tolerances for each of the other objective function. If the difference between the best score and the current score is less than the tolerance, the individual is considered to have converged
                If an index of the list is None, that item will not be used for early stopping
            -int 
                If an int is given, it will be used as the tolerance for all objectives
        - early_stop : int
            Number of generations without improvement before early stopping. All objectives must have converged within the tolerance for this to be triggered.
        
        - warm_start (bool): If True, will use the continue the evolutionary algorithm from the last generation of the previous run.
         
        - memory: EXPERIMENTAL a Memory object or string, optional (default: None)
            If supplied, pipeline will cache each transformer after calling fit. This feature
            is used to avoid computing the fit transformers within a pipeline if the parameters
            and input data are identical with another fitted pipeline during optimization process.
            String 'auto':
                TPOT uses memory caching with a temporary directory and cleans it up upon shutdown.
            String path of a caching directory
                TPOT uses memory caching with the provided directory and TPOT does NOT clean
                the caching directory up upon shutdown. If the directory does not exist, TPOT will
                create it.
            Memory object:
                TPOT uses the instance of joblib.Memory for memory caching,
                and TPOT does NOT clean the caching directory up upon shutdown.
            None:
                TPOT does not use memory caching.
        - cross_val_predict_cv (int): Number of folds to use for the cross_val_predict function for inner classifiers and regressors. Estimators will still be fit on the full dataset, but the following node will get the outputs from cross_val_predict.
                0-1 : When set to 0 or 1, the cross_val_predict function will not be used. The next layer will get the outputs from fitting and transforming the full dataset.
                n>=2 : When fitting pipelines with inner classifiers or regressors, they will still be fit on the full dataset. 
                        However, the output to the next node will come from cross_val_predict with the specified number of folds.
         
        - budget_range (list): [start, end] EXPERIMENTAL A starting and ending budget to use for the budget scaling.

        - budget_scaling (float): [0,1] EXPERIMENTAL A scaling factor to use when determining how fast we move the budget from the start to end budget.

        - generations_until_max_budget (int): EXPERIMENTAL The number of generations to run before reaching the max budget.

        - preprocessing : EXPERIMENTAL
            bool : If True, will use a default preprocessing pipeline.
            Pipeline : If an instance of a pipeline is given, will use that pipeline as the preprocessing pipeline.
         
        - validation_strategy (str): EXPERIMENTAL The validation strategy to use for selecting the final pipeline from the population. TPOT2 may overfit the cross validation score. A second validation set can be used to select the final pipeline.
            - 'auto' : Automatically determine the validation strategy based on the dataset shape.
            - 'reshuffled' : Use the same data for cross validation and final validation, but with different splits for the folds. This is the default for small datasets. 
            - 'split' : Use a separate validation set for final validation. Data will be split according to validation_fraction. This is the default for medium datasets. 
            - 'none' : Do not use a separate validation set for final validation. Select based on the original cross-validation score. This is the default for large datasets.

        - validation_fraction (float): EXPERIMENTAL The fraction of the dataset to use for the validation set when validation_strategy is 'split'. Must be between 0 and 1.
        
        - subset_column : str or int: EXPERIMENTAL The column to use for the subset selection. Must also pass in unique_subset_values to GraphIndividual to function.
         
        - stepwise_steps (int): EXPERIMENTAL The number of staircase steps to take when scaling the budget and population size.

        '''


        self.callback=callback
        self.population_size = population_size
        self.generations = generations
        self.n_jobs= n_jobs
        self.scorers = scorers

        self.warm_start=warm_start
        self.initial_population_size = initial_population_size
        if self.initial_population_size is None:
            self._initial_population_size = self.population_size
        else:
            self._initial_population_size = self.initial_population_size

        if isinstance(self.scorers, str):
            self._scorers = [self.scorers]

        elif callable(self.scorers):
            self._scorers = [self.scorers]
        else:
            self._scorers = self.scorers
        
        self._scorers = [sklearn.metrics.get_scorer(scoring) for scoring in self._scorers]

        self.bigger_is_better = bigger_is_better

        self.cv = cv
        self.other_objective_functions = other_objective_functions

        self.evolver = evolver
        if isinstance(self.evolver, str):
            self._evolver = EVOLVERS[self.evolver]
        else:
            self._evolver = self.evolver
        
        self.evolver_params  = evolver_params

        self.scorers_weights = scorers_weights
        self.other_objective_functions_weights = other_objective_functions_weights

        self.verbose = verbose

        self.max_depth = max_depth
        self.max_size = max_size
        self.max_children = max_children

        self.inner_config_dict= inner_config_dict
        self.root_config_dict= root_config_dict
        self.leaf_config_dict= leaf_config_dict

        self.max_time_seconds =max_time_seconds 
        self.max_eval_time_seconds = max_eval_time_seconds
        self.classification = classification

        self.periodic_checkpoint_folder = periodic_checkpoint_folder

        self.n_initial_optimizations  = n_initial_optimizations  
        self.optimization_cv  = optimization_cv
        self.max_optimize_time_seconds = max_optimize_time_seconds 
        self.optimization_steps = optimization_steps 

        self.threshold_evaluation_early_stop =threshold_evaluation_early_stop
        self.threshold_evaluation_scaling =  threshold_evaluation_scaling
        self.min_history_threshold = min_history_threshold

        self.selection_evaluation_early_stop = selection_evaluation_early_stop
        self.selection_evaluation_scaling =  selection_evaluation_scaling
        
        self.population_scaling = population_scaling
        self.generations_until_end_population = generations_until_end_population

        self.subsets = subsets

        #Initialize other used params
        self.objective_function_weights = [*scorers_weights, *other_objective_functions_weights]
        
        self.objective_names = [f._score_func.__name__ if hasattr(f,"_score_func") else f.__name__ for f in self._scorers] + [f.__name__ for f in other_objective_functions]
        self.scorers_early_stop_tol = scorers_early_stop_tol
        self._scorers_early_stop_tol = self.scorers_early_stop_tol
        self.other_objectives_early_stop_tol = other_objectives_early_stop_tol
        self.early_stop = early_stop
        self.memory = memory
        self.cross_val_predict_cv = cross_val_predict_cv

        self.budget_range = budget_range
        self.budget_scaling = budget_scaling
        self.generations_until_end_budget = generations_until_end_budget
        self.preprocessing = preprocessing

        self.validation_strategy = validation_strategy
        self.validation_fraction = validation_fraction

        self.subset_column = subset_column
        self.stepwise_steps = stepwise_steps

        if not isinstance(self.other_objectives_early_stop_tol, list):
            self._other_objectives_early_stop_tol = [self.other_objectives_early_stop_tol for _ in range(len(self.other_objective_functions))]
        else:
            self._other_objectives_early_stop_tol = self.other_objectives_early_stop_tol

        if not isinstance(self._scorers_early_stop_tol, list):
            self._scorers_early_stop_tol = [self._scorers_early_stop_tol for _ in range(len(self._scorers))]
        else:
            self._scorers_early_stop_tol = self._scorers_early_stop_tol

        self.early_stop_tol = [*self._scorers_early_stop_tol, *self._other_objectives_early_stop_tol]
        
        self._evolver_instance = None
        self.evaluated_individuals = None


    def fit(self, X, y):

        self.evaluated_individuals = None
        #determine validation strategy
        if self.validation_strategy == 'auto':
            nrows = X.shape[0]
            ncols = X.shape[1]

            if nrows/ncols < 20:
                validation_strategy = 'reshuffled'
            elif nrows/ncols < 100:
                validation_strategy = 'split'
            else:
                validation_strategy = 'none'
        else:
            validation_strategy = self.validation_strategy

        if validation_strategy == 'split':
            if self.classification:
                X, X_val, y, y_val = train_test_split(X, y, test_size=self.validation_fraction, stratify=y, random_state=42)
            else:
                X, X_val, y, y_val = train_test_split(X, y, test_size=self.validation_fraction, random_state=42)


        X_original = X
        if self.preprocessing:
            X = pd.DataFrame(X)
            self._preprocessing_pipeline = sklearn.pipeline.make_pipeline(tpot2.CatImpute(), tpot2.NumericImpute(), tpot2.CatOneHotEncoder(),sklearn.preprocessing.StandardScaler())
            X = self._preprocessing_pipeline.fit_transform(X)
        else:
            self._preprocessing_pipeline = None

        _, y = sklearn.utils.check_X_y(X, y, y_numeric=True)

        #Set up the configuation dictionaries and the search spaces
        n_samples=X.shape[0]
        n_features=X.shape[1]

        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns
        else:
            self.feature_names = None

        if self.root_config_dict == 'Auto':
            if self.classification:
                root_config_dict = get_configuration_dictionary("classifiers", n_samples, n_features, self.classification, subsets=self.subsets, feature_names=self.feature_names)
            else:
                root_config_dict = get_configuration_dictionary("regressors", n_samples, n_features, self.classification,subsets=self.subsets, feature_names=self.feature_names)
        else:
            root_config_dict = get_configuration_dictionary(self.root_config_dict, n_samples, n_features, self.classification, subsets=self.subsets,feature_names=self.feature_names)

        inner_config_dict = get_configuration_dictionary(self.inner_config_dict, n_samples, n_features, self.classification,subsets=self.subsets, feature_names=self.feature_names)
        leaf_config_dict = get_configuration_dictionary(self.leaf_config_dict, n_samples, n_features, self.classification, subsets=self.subsets, feature_names=self.feature_names)

        if self.n_initial_optimizations > 0:
            tmp = partial(tpot2.estimator_objective_functions.cross_val_score_objective,scorers= self._scorers, cv=self.optimization_cv )
            optuna_objective = lambda ind: tmp(
                ind.export_pipeline(memory=self.memory, cross_val_predict_cv=self.cross_val_predict_cv, subset_column=self.subset_column), 
                X, y, )
        else:
            optuna_objective = None



        self.cv_gen = sklearn.model_selection.check_cv(self.cv, y, classifier=self.classification)
        self.cv_gen.shuffle = True
        self.cv_gen.random_state = 1

        self.individual_generator_instance = tpot2.estimator_graph_individual_generator(   
                                                            inner_config_dict=inner_config_dict,
                                                            root_config_dict=root_config_dict,
                                                            leaf_config_dict=leaf_config_dict,
                                                            max_depth = self.max_depth,
                                                            max_size = self.max_size,
                                                            max_children = self.max_children,
                                                                )

        if self.threshold_evaluation_early_stop is not None or self.selection_evaluation_early_stop is not None:
            evalutation_early_stop_steps = self.cv
        else:
            evalutation_early_stop_steps = None


        def objective_function_generator(pipeline, x,y, scorers, cv, other_objective_functions, step=None, budget=None, generation=1,is_classification=True):
            #subsample the data
            if budget is not None and budget < 1:
                if is_classification:
                    x,y = sklearn.utils.resample(x,y, stratify=y, n_samples=int(budget*len(x)), replace=False, random_state=1)
                else:
                    x,y = sklearn.utils.resample(x,y, n_samples=int(budget*len(x)), replace=False, random_state=1)

            cv_obj_scores = tpot2.estimator_objective_functions.cross_val_score_objective(sklearn.base.clone(pipeline),x,y,scorers=scorers, cv=cv , fold=step)
            
            other_scores = []
            
            if other_objective_functions is not None and len(other_objective_functions) >0:
                other_scores = [obj(sklearn.base.clone(pipeline)) for obj in other_objective_functions]
            
            return np.concatenate([cv_obj_scores,other_scores])

        #tmp = partial(objective_function_generator, scorers= self._scorers, cv=self.cv_gen, other_objective_functions=self.other_objective_functions )
        self.final_object_function_list = [lambda pipeline_individual, **kwargs: objective_function_generator(
                pipeline_individual.export_pipeline(memory=self.memory, cross_val_predict_cv=self.cross_val_predict_cv, subset_column=self.subset_column),
                #ind,
                X, y, 
                is_classification=self.classification,
                scorers= self._scorers, cv=self.cv_gen, other_objective_functions=self.other_objective_functions,
                **kwargs,
                )]


        #If warm start and we have an evolver instance, use the existing one
        if not(self.warm_start and self._evolver_instance is not None):
            self._evolver_instance = self._evolver(   individual_generator=self.individual_generator_instance, 
                                            objective_functions=self.final_object_function_list,
                                            objective_function_weights = self.objective_function_weights,
                                            objective_names=self.objective_names,
                                            bigger_is_better = self.bigger_is_better,
                                            population_size= self.population_size,
                                            generations=self.generations,
                                            initial_population_size = self._initial_population_size,
                                            n_jobs=self.n_jobs,
                                            verbose = self.verbose,
                                            max_time_seconds =      self.max_time_seconds ,
                                            max_eval_time_seconds = self.max_eval_time_seconds,
                                            optimization_objective=optuna_objective,
                                            periodic_checkpoint_folder = self.periodic_checkpoint_folder,
                                            threshold_evaluation_early_stop = self.threshold_evaluation_early_stop,
                                            threshold_evaluation_scaling =  self.threshold_evaluation_scaling,
                                            min_history_threshold = self.min_history_threshold,

                                            selection_evaluation_early_stop = self.selection_evaluation_early_stop,
                                            selection_evaluation_scaling =  self.selection_evaluation_scaling,
                                            evalutation_early_stop_steps = evalutation_early_stop_steps,

                                            early_stop_tol = self.early_stop_tol,
                                            early_stop= self.early_stop,
                                            
                                            budget_range = self.budget_range,
                                            budget_scaling = self.budget_scaling,
                                            generations_until_end_budget = self.generations_until_end_budget,

                                            population_scaling = self.population_scaling,
                                            generations_until_end_population = self.generations_until_end_population,
                                            stepwise_steps = self.stepwise_steps,
                                            **self.evolver_params)

        
        self._evolver_instance.optimize()
        self._evolver_instance.population.update_pareto_fronts(self.objective_names, self.objective_function_weights)
        self.make_evaluated_individuals()

        if validation_strategy == 'reshuffled':
            best_pareto_front_idx = list(self.pareto_front.index)
            best_pareto_front = self.pareto_front.loc[best_pareto_front_idx]['Instance']
            
            #reshuffle rows
            X, y = sklearn.utils.shuffle(X, y, random_state=1)

            val_objective_function_list = [lambda ind, **kwargs: objective_function_generator(
                ind,
                X,y, 
                is_classification=self.classification,
                scorers= self._scorers, cv=self.cv_gen, other_objective_functions=self.other_objective_functions,
                **kwargs,
                )]
            
            val_scores = tpot2.objectives.parallel_eval_objective_list(
                best_pareto_front,
                val_objective_function_list, n_jobs=self.n_jobs, verbose=self.verbose, timeout=self.max_eval_time_seconds,n_expected_columns=len(self.objective_names))

            val_objective_names = ['validation_'+name for name in self.objective_names]
            self.objective_names_for_selection = val_objective_names
            self.evaluated_individuals.loc[best_pareto_front_idx,val_objective_names] = val_scores

        elif validation_strategy == 'split':

                
            def val_objective_function_generator(pipeline, X_train, y_train, X_test, y_test, scorers, other_objective_functions):
                #subsample the data
                fitted_pipeline = sklearn.base.clone(pipeline)
                fitted_pipeline.fit(X_train, y_train)

                this_fold_scores = [sklearn.metrics.get_scorer(scorer)(fitted_pipeline, X_test, y_test) for scorer in scorers] 
                
                other_scores = []
                #TODO use same exported pipeline as for each objective
                if other_objective_functions is not None and len(other_objective_functions) >0:
                    other_scores = [obj(sklearn.base.clone(pipeline)) for obj in other_objective_functions]
                
                return np.concatenate([this_fold_scores,other_scores])

            best_pareto_front_idx = list(self.pareto_front.index)
            best_pareto_front = self.pareto_front.loc[best_pareto_front_idx]['Instance']
            val_objective_function_list = [lambda ind, **kwargs: val_objective_function_generator(
                ind,
                X,y,
                X_val, y_val, 
                scorers= self._scorers, other_objective_functions=self.other_objective_functions,
                **kwargs,
                )]
            
            val_scores = tpot2.objectives.parallel_eval_objective_list(
                best_pareto_front,
                val_objective_function_list, n_jobs=self.n_jobs, verbose=self.verbose, timeout=self.max_eval_time_seconds,n_expected_columns=len(self.objective_names))

            val_objective_names = ['validation_'+name for name in self.objective_names]
            self.objective_names_for_selection = val_objective_names
            self.evaluated_individuals.loc[best_pareto_front_idx,val_objective_names] = val_scores
        else:
            self.objective_names_for_selection = self.objective_names

        val_scores = self.evaluated_individuals[~self.evaluated_individuals[self.objective_names_for_selection].isin(["TIMEOUT","INVALID"]).any(axis=1)][self.objective_names_for_selection].astype(float)                                     
        weighted_scores = val_scores*self.objective_function_weights
        
        if self.bigger_is_better:
            best_idx = weighted_scores[self.objective_names_for_selection[0]].idxmax()
        else:
            best_idx = weighted_scores[self.objective_names_for_selection[0]].idxmin()
        
        best_individual = self.evaluated_individuals.loc[best_idx]['Individual']
        self.selected_best_score =  self.evaluated_individuals.loc[best_idx]
        

        best_individual_pipeline = best_individual.export_pipeline(memory=self.memory, cross_val_predict_cv=self.cross_val_predict_cv, subset_column=self.subset_column)

        if self.preprocessing:
            self.fitted_pipeline_ = sklearn.pipeline.make_pipeline(sklearn.base.clone(self._preprocessing_pipeline), best_individual_pipeline )
        else:
            self.fitted_pipeline_ = best_individual_pipeline 
        
        self.fitted_pipeline_.fit(X_original,y) #TODO use y_original as well?
        if self.verbose >= 3:
            best_individual.plot()

    def _estimator_has(attr):
        '''Check if we can delegate a method to the underlying estimator.
        First, we check the first fitted final estimator if available, otherwise we
        check the unfitted final estimator.
        '''
        return  lambda self: (self.fitted_pipeline_ is not None and
            hasattr(self.fitted_pipeline_, attr)
        )


    @available_if(_estimator_has('predict'))
    def predict(self, X, **predict_params):
        check_is_fitted(self)
        #X = check_array(X)
        return self.fitted_pipeline_.predict(X,**predict_params)
    
    @available_if(_estimator_has('predict_proba'))
    def predict_proba(self, X, **predict_params):
        check_is_fitted(self)
        #X = check_array(X)
        return self.fitted_pipeline_.predict_proba(X,**predict_params)
    
    @available_if(_estimator_has('decision_function'))
    def decision_function(self, X, **predict_params):
        check_is_fitted(self)
        #X = check_array(X)
        return self.fitted_pipeline_.decision_function(X,**predict_params)
    
    @available_if(_estimator_has('transform'))
    def transform(self, X, **predict_params):
        check_is_fitted(self)
        #X = check_array(X)
        return self.fitted_pipeline_.transform(X,**predict_params)

    @property
    def classes_(self):
        """The classes labels. Only exist if the last step is a classifier."""
        return self.fitted_pipeline_.classes_


    def make_evaluated_individuals(self):
        #check if _evolver_instance exists
        if self.evaluated_individuals is None:
            self.evaluated_individuals  =  self._evolver_instance.population.evaluated_individuals.copy()
            objects = list(self.evaluated_individuals.index)
            object_to_int = dict(zip(objects, range(len(objects))))
            self.evaluated_individuals = self.evaluated_individuals.set_index(self.evaluated_individuals.index.map(object_to_int))
            self.evaluated_individuals['Parents'] = self.evaluated_individuals['Parents'].apply(lambda row: _convert_parents_tuples_to_integers(row, object_to_int))

            self.evaluated_individuals["Instance"] = self.evaluated_individuals["Individual"].apply(lambda ind: _apply_make_pipeline(ind, preprocessing_pipeline=self._preprocessing_pipeline))

        return self.evaluated_individuals
        
    @property
    def pareto_front(self):
        #check if _evolver_instance exists
        if self.evaluated_individuals is None:
            return None
        else:
            if "Pareto_Front" not in self.evaluated_individuals:
                return self.evaluated_individuals
            else:
                return self.evaluated_individuals[self.evaluated_individuals["Pareto_Front"]==0]


def _convert_parents_tuples_to_integers(row, object_to_int):
    if type(row) == list or type(row) == np.ndarray or type(row) == tuple:
        return tuple(object_to_int[obj] for obj in row)
    else:
        return np.nan

def _apply_make_pipeline(graphindividual, preprocessing_pipeline=None):
    if preprocessing_pipeline is None:
        return graphindividual.export_pipeline()
    else:
        return sklearn.pipeline.make_pipeline(sklearn.base.clone(preprocessing_pipeline), graphindividual.export_pipeline())


def get_configuration_dictionary(options, n_samples, n_features, classification, subsets=None, feature_names=None):
    if options is None:
        return options

    if isinstance(options, dict):
        return recursive_with_defaults(options, n_samples, n_features, classification, subsets=subsets, feature_names=feature_names)
    
    if not isinstance(options, list):
        options = [options]

    config_dict = {}

    for option in options:

        if option == "selectors":
            config_dict.update(tpot2.config.make_selector_config_dictionary(classification))

        elif option == "classifiers":
            config_dict.update(tpot2.config.make_classifier_config_dictionary(n_samples=n_samples))

        elif option == "regressors":
            config_dict.update(tpot2.config.make_regressor_config_dictionary(n_samples=n_samples))

        elif option == "transformers":
            config_dict.update(tpot2.config.make_transformer_config_dictionary(n_features=n_features))
        
        elif option == "arithmetic_transformer":
            config_dict.update(tpot2.config.make_arithmetic_transformer_config_dictionary())

        elif option == "feature_set_selector":
            config_dict.update(tpot2.config.make_FSS_config_dictionary(subsets, n_features, feature_names=feature_names))

        elif option == "passthrough":
            config_dict.update(tpot2.config.make_passthrough_config_dictionary())

        else:
            config_dict.update(recursive_with_defaults(option, n_samples, n_features, classification, subsets=subsets, feature_names=feature_names))

    if len(config_dict) == 0:
        raise ValueError("No valid configuration options were provided. Please check the options you provided and try again.")

    return config_dict

def recursive_with_defaults(config_dict, n_samples, n_features, classification, subsets=None, feature_names=None):
    
    for key in 'leaf_config_dict', 'root_config_dict', 'inner_config_dict', 'Recursive':
        if key in config_dict:
            value = config_dict[key]
            if key=="Resursive":
                config_dict[key] = recursive_with_defaults(value,n_samples, n_features, classification, subsets=None, feature_names=None)
            else:
                config_dict[key] = get_configuration_dictionary(value, n_samples, n_features, classification, subsets, feature_names)
        
    return config_dict