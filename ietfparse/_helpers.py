from __future__ import annotations

from ietfparse import errors


class ParameterParser:
    """Utility class to parse Link headers.

    :param strict: controls whether parsing follows all of
        the rules laid out in :rfc:`5988`

    This class parses the parameters for a single :mailheader:`Link`
    value.  It is used from within the guts of
    :function:`ietfparse.headers.parse_link_header` and not readily
    suited for other uses.  If *strict mode* is enabled, then the
    following rules from the RFC are obeyed:

    - section 5.3: when multiple "rel" attributes are present, then
      the first one is chosen.  The remaining are omitted from the
      value set.
    - section 5.4: "there MUST NOT be more than one media parameter".
      If more than one is present, then ``MalformedLinkValue`` is
      raised.
    - section 5.4: when multiple "type" attributes are present, then
      the first one is chosen.  The remaining are omitted form the
      value set.
    - section 5.4: when multiple "title" attributes are present, then
      the first one is chosen.  The remaining are omitted form the
      value set.
    - section 5.4: if both "title" and "title*" are present, then
      "title*" is preferred.  The value of "title*" will be used
      in all cases.
    - section 5.4: "there MUST NOT be more than one type parameter".
      If more than one is present, then ``MalformedLinkValue`` is
      raised.

    """

    def __init__(self, *, strict: bool = True) -> None:
        self.strict = strict
        self._values: list[tuple[str, str]] = []
        self._rfc_values: dict[str, str | None] = {
            'rel': None,
            'media': None,
            'type': None,
            'title': None,
            'title*': None,
        }

    def add_value(self, name: str, value: str) -> None:
        """Add a new value to the list.

        :param str name: name of the value that is being parsed
        :param str value: value that is being parsed
        :raises ietfparse.errors.MalformedLinkValue:
            if *strict mode* is enabled and a validation error
            is detected

        This method implements most of the validation mentioned in
        sections 5.3 and 5.4 of :rfc:`5988`.  The ``_rfc_values``
        dictionary contains the appropriate values for the attributes
        that get special handling.  If *strict mode* is enabled, then
        only values that are acceptable will be added to ``_values``.

        """
        try:
            if self._rfc_values[name] is None:
                self._rfc_values[name] = value
            elif self.strict:
                if name in ('media', 'type'):
                    msg = f'More than one {name} parameter present'
                    raise errors.MalformedLinkValue(msg)
                return
        except KeyError:
            pass

        if self.strict and name in ('title', 'title*'):
            return

        self._values.append((name, value))

    @property
    def values(self) -> list[tuple[str, str]]:
        """The name/value mapping that was parsed."""
        values = self._values[:]
        if self.strict:
            preferred_title = self._rfc_values['title*']
            fallback_title = self._rfc_values['title']
            if preferred_title is not None:
                values.append(('title*', preferred_title))
                if fallback_title is not None:
                    values.append(('title', preferred_title))
            elif fallback_title is not None:
                values.append(('title', fallback_title))
        return values
