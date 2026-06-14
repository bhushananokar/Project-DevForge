"""Allow running as: python -m todo"""

import sys
from .cli import main

sys.exit(main())
