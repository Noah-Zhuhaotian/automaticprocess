"""Wizard step mixins, composed together by app.gui.main_window.MainWindow.

Each module defines one mixin class holding that step's tk variables
(initialized via an `_init_*_vars` method) plus its build/validate/helper
methods. Every method still assumes `self` is the final composed
MainWindow instance - e.g. a step's build method may reference another
step's widgets or call MainWindow's own navigation methods - so these
mixins are not meant to be instantiated on their own.
"""
