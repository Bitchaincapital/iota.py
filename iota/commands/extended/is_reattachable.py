# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from typing import List

import filters as f

from iota import Address
from iota.commands import FilterCommand, RequestFilter, ResponseFilter
from iota.commands.extended import FindTransactionObjectsCommand, \
    GetLatestInclusionCommand
from iota.filters import Trytes, StringifiedTrytesArray

__all__ = [
    'IsReattachableCommand',
]


class IsReattachableCommand(FilterCommand):
    """
    Executes ``isReattachable`` extended API command.
    """
    command = 'isReattachable'

    def get_request_filter(self):
        return IsReattachableRequestFilter()

    def get_response_filter(self):
        return IsReattachableResponseFilter()

    def _execute(self, request):
        addresses = request['addresses']  # type: List[Address]

        # fetch full transaction objects
        transactions = FindTransactionObjectsCommand(adapter=self.adapter)(
            addresses=addresses,
        )['transactions']

        # Map and filter transactions which have zero value.
        # If multiple transactions for the same address are returned,
        # the one with the highest ``attachment_timestamp`` is selected.
        transactions = sorted(
            transactions,
            key=lambda t: t.attachment_timestamp
        )

        transaction_map = {
            t.address: t.hash
            for t in transactions
            if t.value > 0
        }

        # Fetch inclusion states.
        inclusion_states = GetLatestInclusionCommand(adapter=self.adapter)(
            hashes=list(transaction_map.values()),
        )
        inclusion_states = inclusion_states['states']

        return {
            'reattachable': [
                not inclusion_states[transaction_map[address]]
                for address in addresses
            ],
        }


class IsReattachableRequestFilter(RequestFilter):
    def __init__(self):
        super(IsReattachableRequestFilter, self).__init__(
            {
                'addresses': StringifiedTrytesArray(Address) | f.Required,
            },
        )


class IsReattachableResponseFilter(ResponseFilter):
    def __init__(self):
        super(IsReattachableResponseFilter, self).__init__({
            'reattachable':
                f.Required | f.Array | f.FilterRepeater(f.Type(bool)),
        })
