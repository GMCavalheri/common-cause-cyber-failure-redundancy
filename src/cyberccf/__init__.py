"""Redundancy that one cyber attack can defeat.

``cyberccf`` extends the classical beta-factor common-cause failure (CCF) model, built for
shared physical causes such as one power supply feeding "redundant" channels, to shared cyber
vulnerabilities: identical firmware, a shared network segment or a shared supply-chain part
that lets a single attack defeat every channel at once. It quantifies how much of the
reliability benefit claimed for redundancy survives once that is modelled, and what design
diversity buys back, on a synthetic navigation architecture.
"""

__version__ = "1.0.0"
