def tf(v):
    """ Turns columns with values yes & no to Boolean"""
    if v == "yes":
        return True
    elif v == "no":
        return False
    else:
        raise ValueError(v)
