import numpy as np

def tf(v):
    """ Turns columns with values yes & no to Boolean"""
    if v == "yes":
        return True
    elif v == "no":
        return False
    else:
        raise ValueError(v)

def probability_to_boolean(p):
    return p > 0.5

def compute_predictive_accuracy(predicted, true):
    return np.mean(probability_to_boolean(predicted)==probability_to_boolean(true.apply(tf)))

def compute_predictive_accuracy_per_state(state, target, df_predictions, df_test):
    df_test_state = df_test[df_test.state==state]
    df_predictions_state = df_predictions[df_test.state==state]
    return compute_predictive_accuracy(df_predictions_state[target], df_test_state[target])
