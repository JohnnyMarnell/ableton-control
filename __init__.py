from .AbletonControlSurface import AbletonControlSurface

""" Bootstrap the control surface """
def create_instance(c_instance):
    return AbletonControlSurface(c_instance)