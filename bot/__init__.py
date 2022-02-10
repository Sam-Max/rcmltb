#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "1.0.0"
__author__ = ""

#
import logging
from .core.varholdern import VarHolder
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("botlog.txt")]
)

uptime = time.time()
SessionVars = VarHolder()
