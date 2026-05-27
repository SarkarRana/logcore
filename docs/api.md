# API reference

Everything below is auto-generated from the docstrings in the source. Private members (anything starting with `_`) are excluded.

## Top-level exports

```{eval-rst}
.. currentmodule:: logcore

.. autosummary::
   :nosignatures:

   get_logger
   Sampler
   LogLevel
   set_correlation_id
   get_correlation_id
```

## Logger

```{eval-rst}
.. autofunction:: logcore.get_logger
```

```{eval-rst}
.. autoclass:: logcore.logger.LogCoreLogger
   :members:
   :member-order: bysource
```

## Sampling

```{eval-rst}
.. autoclass:: logcore.sampling.Sampler
   :members:
   :member-order: bysource
```

```{eval-rst}
.. autoclass:: logcore.sampling.SamplerStats
   :members:
```

```{eval-rst}
.. autoclass:: logcore.sampling.Decision
   :members:
   :undoc-members:
```

```{eval-rst}
.. autofunction:: logcore.sampling.sampler_from_env
```

## Correlation IDs

```{eval-rst}
.. autofunction:: logcore.set_correlation_id
```

```{eval-rst}
.. autofunction:: logcore.get_correlation_id
```

```{eval-rst}
.. autofunction:: logcore.utils.correlation_id_context
```

## Timing helpers

```{eval-rst}
.. autoclass:: logcore.utils.Timer
   :members:
```

```{eval-rst}
.. autoclass:: logcore.utils.AsyncTimer
   :members:
```

## Configuration

```{eval-rst}
.. autoclass:: logcore.config.LogCoreConfig
   :members:
```

```{eval-rst}
.. autoclass:: logcore.LogLevel
   :members:
   :undoc-members:
```

```{eval-rst}
.. autofunction:: logcore.config.create_config
```

## Formatters

```{eval-rst}
.. autoclass:: logcore.formatters.JSONFormatter
   :members:
```

```{eval-rst}
.. autoclass:: logcore.formatters.TextFormatter
   :members:
```

```{eval-rst}
.. autoclass:: logcore.formatters.RedactingFormatter
   :members:
```

## Handlers

```{eval-rst}
.. autoclass:: logcore.handlers.ConsoleHandler
   :members:
```

```{eval-rst}
.. autoclass:: logcore.handlers.FileHandler
   :members:
```

```{eval-rst}
.. autofunction:: logcore.handlers.create_handlers
```
