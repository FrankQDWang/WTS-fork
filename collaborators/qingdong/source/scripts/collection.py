"""Compile retained-list collection using only the host's existing page DSL."""
from __future__ import annotations

import copy


def state_schema(channel):
    selectors = channel['selectors']
    return {'fields': {
        'url': {'source': 'page.url'},
        'query': {'source': 'value', 'locator': {'any_css': selectors['keyword_inputs'], 'visible': True}},
        'filters': {'source': 'texts', 'locator': {'any_css': selectors['submitted_filter_chips']}},
        'page': {'source': 'text', 'locator': {'any_css': selectors['active_page']}},
    }}


def snapshot_step(channel, name='capture-list-state'):
    return {'id': name, 'op': 'page.extract', 'schema': state_schema(channel), 'save_as': 'search.list_state'}


def variable(path, value):
    return {'type': 'variable', 'path': path, 'operator': 'equals', 'value': value, 'case_sensitive': True}


def prepare_collection(steps, channel, card_schema, prior, restore_search=False):
    """Reuse a verified snapshot, otherwise restore the query on the search page."""
    if not restore_search:
        steps[:] = [s for s in steps if s['action'] != 'page.navigate']
    search = next(s for s in steps if s['id'] == 'search-and-extract-cards')
    original = search['program']
    split = next(i for i, s in enumerate(original) if s['id'] == 'initialize-card-buffer')
    snapshot = prior.get('list_state')
    reusable = (isinstance(snapshot, dict) and isinstance(snapshot.get('url'), str)
                and '/search/getConditionItem' in snapshot['url']
                and isinstance(snapshot.get('query'), str)
                and isinstance(snapshot.get('filters'), list)
                and all(isinstance(x, str) for x in snapshot['filters'])
                and isinstance(snapshot.get('page'), str))
    same = {'all': [variable(f'search.list_state.{key}', snapshot[key])
                    for key in ('url', 'query', 'page')] +
                   [variable('search.list_state.filters.length', len(snapshot['filters']))] +
                   [variable(f'search.list_state.filters.{i}', value)
                    for i, value in enumerate(snapshot['filters'])]} if reusable else False
    search['program'] = [
        original[0],  # Preserve login/risk detection before any interaction.
        {'id': 'collect-search-page-required', 'op': 'page.wait',
         'until': {'all': [{'url_contains': ['/search/getConditionItem']},
                           {'any_visible': channel['selectors']['keyword_inputs']},
                           {'none_visible': channel['selectors']['loading']}]},
         'timeout_ms': channel['timing']['search_timeout_ms']},
        snapshot_step(channel),
        {'id': 'initialize-unsupported-filter-buffer', 'op': 'data.set',
         'path': 'search.unsupported_filters', 'value': prior.get('unsupported_filters', [])},
        {'id': 'restore-search-if-changed', 'op': 'flow.if',
         'condition': False if restore_search else same, 'then': [], 'else': original[1:split]},
        # Original selected cards drive failures too; missing cards cannot silently disappear.
        {'id': 'restore-selected-cards', 'op': 'data.set', 'path': 'search.cards', 'value': prior['cards']},
        {'id': 'restore-card-pages', 'op': 'data.set', 'path': 'search.pages', 'value': prior.get('pages', [])},
        snapshot_step(channel, 'capture-collected-list-state'),
    ]
    detail = next(s for s in steps if s['id'] == 'collect-candidate-details')
    opening = detail['open']
    # Re-read stable identities just before every click; never reuse a stale row index.
    identity_schema = copy.deepcopy(card_schema)
    identity_schema['fields'] = {k: v for k, v in identity_schema['fields'].items()
                                 if k in ('source_candidate_id', 'candidate_ref', 'row_index')}
    opening['pre_program'] += [
        {'id': 'remember-selected-candidate', 'op': 'data.set', 'path': 'collect.wanted',
         'value': {'$item': 'candidate_ref'}},
        {'id': 'initialize-identity-matches', 'op': 'data.set', 'path': 'collect.matches', 'value': []},
        {'id': 'read-live-card-identities', 'op': 'page.extract_list', 'root': card_schema['root'],
         'schema': identity_schema, 'limit': 30, 'save_as': 'collect.live_cards'},
        {'id': 'locate-selected-candidate', 'op': 'flow.foreach', 'items': {'$ref': 'collect.live_cards'},
         'max_iterations': 30, 'program': [
             {'id': 'match-candidate-ref', 'op': 'flow.if',
              'condition': variable('collect.wanted', {'$item': 'candidate_ref'}),
              'then': [{'id': 'remember-live-row', 'op': 'data.append', 'path': 'collect.matches',
                        'value': {'$item': 'row_index'}, 'max_items': 30}], 'else': []}]},
        {'id': 'require-unique-selected-candidate', 'op': 'page.wait',
         'until': variable('collect.matches.length', 1), 'timeout_ms': 100},
    ]
    opening['target']['within']['index'] = {'$ref': 'collect.matches.0'}
    return steps
