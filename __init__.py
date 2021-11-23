from .AbletonPythonResticleControlSurface import AbletonPythonResticleControlSurface

""" Bootstrap the control surface """
def create_instance(c_instance):
    return AbletonPythonResticleControlSurface(c_instance)