import logging
from pprint import pprint

from adwords_client.client import AdWords
from adwords_client import reports
from adwords_client.internal_api.builder import OperationsBuilder

logging.basicConfig(level=logging.INFO)
logging.getLogger('googleads').setLevel(logging.ERROR)
logging.getLogger('oauth2client').setLevel(logging.ERROR)
logging.getLogger('suds').setLevel(logging.WARNING)


def _delete_campaigns():
	client = AdWords(workdir='./tests/generated_files')
	new_report_df = reports.get_campaigns_report(client, 7857288943, 'CampaignStatus != "REMOVED"')
	for campaign in new_report_df:
		entry = {
			'object_type': 'campaign',
			'client_id': 7857288943,
			'campaign_id': campaign['CampaignId'],
			'campaign_name': 'API test campaign',
			'operator': 'SET',
			'status': 'REMOVED',
		}
		client.insert(entry)
	operations_folder = client.split()
	client.execute_operations(operations_folder)
	client.wait_jobs(operations_folder)


def _create_campaign():
	client = AdWords(workdir='./tests/generated_files')
	client.insert(
		{
			'object_type': 'campaign',
			'client_id': 7857288943,
			'campaign_id': -1,
			'budget': 1000,
			'campaign_name': 'API test campaign',
			'locations': [1001773, 1001768],  # Sao Paulo, Sao Caetano
			'languages': [1014, 1000],  # Portuguese, English
		}
	)
	client.insert(
		{
			'object_type': 'adgroup',
			'client_id': 7857288943,
			'campaign_id': -1,
			'adgroup_id': -2,
			'adgroup_name': 'API test adgroup',
		}
	)
	client.insert(
		{
			'object_type': 'keyword',
			'client_id': 7857288943,
			'campaign_id': -1,
			'adgroup_id': -2,
			'text': 'my search term',
			'keyword_match_type': 'broad',
			'status': 'paused',
			'cpc_bid': 13.37,
		}
	)
	client.insert(
		{
			'object_type': 'ad',
			'client_id': 7857288943,
			'campaign_id': -1,
			'adgroup_id': -2,
			'headline_part_1': 'Ad test',
			'headline_part_2': 'my pretty test',
			'description': 'This is my test ad',
			'path_1': 'test',
			'path_2': 'ad',
			'final_urls': 'http://www.mytest.com/',
			'final_mobile_urls': 'http://m.mytest.com/',
		}
	)
	operations_folder = client.split()
	client.execute_operations(operations_folder)
	client.wait_jobs(operations_folder)


def _get_keywords_report(client=None):
	client = client or AdWords(workdir='./tests/generated_files')
	report_df = reports.get_keywords_report(client, 7857288943, 'CampaignStatus = "PAUSED"', fields=True)
	pprint(report_df)
	return report_df


def _adjust_bids():
	client = AdWords(workdir='./tests/generated_files')
	report_df = _get_keywords_report(client)

	for campaign in report_df:
		entry = {
			'object_type': 'keyword',
			'cpc_bid': 4.20,
			'client_id': campaign['ExternalCustomerId'],
			'campaign_id': campaign['CampaignId'],
			'adgroup_id': campaign['AdGroupId'],
			'criteria_id': campaign['Id'],
			'operator': 'SET',
		}
		client.insert(entry)

	operations_folder = client.split()
	client.execute_operations(operations_folder)
	client.wait_jobs(operations_folder)


def _sync_operations():
	client = AdWords()

	get_internal_operation = {
		'object_type': 'shared_set',
		'client_id': 7857288943,
		'fields': ['Name', 'SharedSetId', 'Type', 'Status'],
		'predicates': [
			('Name', 'EQUALS', 'API Sync Test'),
			('Status', 'EQUALS', 'ENABLED'),
		]
	}
	shared_sets = client.get_entities(get_internal_operation)
	for shared_set in shared_sets:
		client.insert({
			'object_type': 'shared_set',
			'client_id': 7857288943,
			'shared_set_id': shared_set['sharedSetId'],
			'operator': 'REMOVE'
		})

	client.execute_operations(sync=True)

	client.insert({
		'object_type': 'shared_set',
		'client_id': 7857288943,
		'shared_set_name': 'API Sync Test',
		'shared_set_type': 'NEGATIVE_KEYWORDS',
	})

	client.execute_operations(sync=True)

	shared_sets = client.get_entities(get_internal_operation)

	for shared_set in shared_sets:
		client.insert({
			'object_type': 'shared_set',
			'client_id': 7857288943,
			'shared_set_id': shared_set['sharedSetId'],
			'operator': 'REMOVE'
		})

	client.execute_operations(sync=True)


def _build_shared_set_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'shared_set',
		'client_id': 7857288943,
		'fields': ['Name', 'SharedSetId', 'Type', 'Status'],
		'predicates': [
			('Name', 'EQUALS', 'API Sync Test'),
			('Status', 'IN', ['ENABLED']),
		]
	}

	get_adwords_operation = next(operation_builder(get_internal_operation))

	expected_get_adwords_operation = {
		'fields': ['Name', 'SharedSetId', 'Type', 'Status'],
		'ordering': [], 'xsi_type': 'Selector',
		'predicates': [
			{
				'values': ['API Sync Test'],
				'field': 'Name',
				'operator': 'EQUALS',
				'xsi_type': 'Predicate'
			},
			{
				'values': ['ENABLED'],
				'field': 'Status',
				'operator': 'IN', 'xsi_type': 'Predicate'
			}
		],
		'paging': {
			'numberResults': 10000,
			'startIndex': 0,
			'xsi_type': 'Paging'
		}
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])

	assert expected_get_adwords_operation == get_adwords_operation


def _build_budget_order_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'budget_order',
		'client_id': 7857288943,
		'fields': ['BillingAccountId', 'PrimaryBillingId', 'Id', 'BillingAccountName'],
		'predicates': [
			('billingAccountName', 'EQUALS', 'Billing Account Test'),
			('PrimaryBillingId', 'EQUALS', "1234-5678-9012"),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'ordering': [],
		'predicates': [
			{
				'values': ['Billing Account Test'],
				'xsi_type': 'Predicate',
				'field': 'billingAccountName',
				'operator': 'EQUALS'},
			{
				'values': ['1234-5678-9012'],
				'xsi_type': 'Predicate',
				'field': 'PrimaryBillingId',
				'operator': 'EQUALS'
			}],
		'xsi_type': 'Selector',
		'fields': ['BillingAccountId', 'PrimaryBillingId', 'Id', 'BillingAccountName'],
		'paging': {'startIndex': 0, 'numberResults': 10000, 'xsi_type': 'Paging'}
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'budget_order',
		'client_id': 7857288943,
		'billing_account_id': '1234-5678-9012-3456',
		'primary_billing_id': '1234-5678-9012',
		'start_date_time': '20361231 235959 America/Los_Angeles',
		'end_date_time': '20371230 235959 America/Los_Angeles',
		'spending_limit': 10000,
		'po_number': 'My Test Reference',
		'budget_order_name': 'Budget Order Name Test',
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))

	expected_mutate_adwords_operation = {
		'operand':
			{
				'budgetOrderName': 'Budget Order Name Test',
				'startDateTime': '20361231 235959 America/Los_Angeles',
				'billingAccountId': '1234-5678-9012-3456',
				'poNumber': 'My Test Reference',
				'spendingLimit': {'microAmount': 10000},
				'endDateTime': '20371230 235959 America/Los_Angeles',
				'primaryBillingId': '1234-5678-9012'
			 },
		'operator': 'ADD'
	}

	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_site_link_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_sitelink',
		'client_id': 7857288943,
		'fields': ['CampaignId', 'Extensions'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))

	expected_get_adwords_operation = {
		'ordering': [],
		'xsi_type': 'Selector',
		'predicates': [{
			'xsi_type': 'Predicate',
			'values': [213213123],
			'field': 'CampaignId',
			'operator': 'EQUALS'
		},{
			'xsi_type': 'Predicate',
			'values': ['SITELINK'],
			'field': 'ExtensionType',
			'operator': 'EQUALS'
		}],
		'paging': {
			'xsi_type': 'Paging',
			'numberResults': 10000,
			'startIndex': 0
		},
		'fields': ['CampaignId', 'Extensions']
	}

	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'campaign_sitelink',
		'client_id': 343434324,
		'sitelinks_configuration':
			[
				{
					'sitelink_text': 'Test 1',
					'sitelink_final_url': 'https://www.example.com.br/'
				},
				{
					'sitelink_text': 'Test 2',
					'sitelink_final_url': 'https://www.example.com.br/example'
				},
				{
					'sitelink_text': 'Test 3',
					'sitelink_final_url': 'https://www.example.com.br/example'
				}
			],
		'campaign_id': 343243243,
	}

	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))

	expected_mutate_adwords_operation = {
		'operator': 'ADD',
		'xsi_type': 'CampaignExtensionSettingOperation',
		'operand': {
			'xsi_type': 'CampaignExtensionSetting',
			'extensionType': 'SITELINK',
			'campaignId': 343243243,
			'extensionSetting':
				{
					'extensions': [
						{
							'sitelinkFinalUrls':
								{
									'urls': ['https://www.example.com.br/']
								},
							'xsi_type': 'SitelinkFeedItem',
							'sitelinkText': 'Test 1'
						},
						{
							'sitelinkFinalUrls':
								{
									'urls': ['https://www.example.com.br/example']
								},
							'xsi_type': 'SitelinkFeedItem',
							'sitelinkText': 'Test 2'
						},
						{
							'sitelinkFinalUrls':
								{
									'urls': ['https://www.example.com.br/example']
								},
							'xsi_type': 'SitelinkFeedItem',
							'sitelinkText': 'Test 3'
						}
					]
				}
		}
	}

	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_structured_snipppet_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_structured_snippet',
		'client_id': 7857288943,
		'fields': ['CampaignId', 'Extensions'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'ordering': [],
		'xsi_type': 'Selector',
		'predicates': [{
			'xsi_type': 'Predicate',
			'values': [213213123],
			'field': 'CampaignId',
			'operator': 'EQUALS'
		},{
			'xsi_type': 'Predicate',
			'values': ['STRUCTURED_SNIPPET'],
			'field': 'ExtensionType',
			'operator': 'EQUALS'
		}],
		'paging': {
			'xsi_type': 'Paging',
			'numberResults': 10000,
			'startIndex': 0
		},
		'fields': ['CampaignId', 'Extensions']
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'campaign_structured_snippet',
		'client_id': 545545354,
		'snippets_configuration': [{
			'header': 'Serviços',
			'values': ['Construção', 'Manutenção', 'Conserto'],
		}],
		'campaign_id': 3232343242
	}

	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))

	expected_mutate_adwords_operation = {
		'xsi_type': 'CampaignExtensionSettingOperation',
		'operator': 'ADD',
		'operand': {
			'extensionSetting': {
				'extensions': [
					{
						'xsi_type': 'StructuredSnippetFeedItem',
						'values': ['Construção', 'Manutenção', 'Conserto'],
						'header': 'Serviços'
					}
				]
			},
			'xsi_type': 'CampaignExtensionSetting',
			'campaignId': 3232343242,
			'extensionType': 'STRUCTURED_SNIPPET'
		}
	}
	mutate_adwords_operation['operand']['extensionSetting']['extensions'][0]['values']\
		= sorted(mutate_adwords_operation['operand']['extensionSetting']['extensions'][0]['values'])
	expected_mutate_adwords_operation['operand']['extensionSetting']['extensions'][0]['values']\
		= sorted(expected_mutate_adwords_operation['operand']['extensionSetting']['extensions'][0]['values'])
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_callout_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_callout',
		'client_id': 7857288943,
		'fields': ['CampaignId', 'Extensions'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))


	expected_get_adwords_operation = {
		'ordering': [],
		'xsi_type': 'Selector',
		'predicates': [{
			'xsi_type': 'Predicate',
			'values': [213213123],
			'field': 'CampaignId',
			'operator': 'EQUALS'
		},{
			'xsi_type': 'Predicate',
			'values': ['CALLOUT'],
			'field': 'ExtensionType',
			'operator': 'EQUALS'
		}],
		'paging': {
			'xsi_type': 'Paging',
			'numberResults': 10000,
			'startIndex': 0
		},
		'fields': ['CampaignId', 'Extensions']
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation


	mutate_internal_operation = {
		'object_type': 'campaign_callout',
		'client_id': 9973876376,
		'callout_text_list': ['Clique aqui','Somos Legais','Contrate aqui'],
		'campaign_id': 1341876198
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operand': {
			'campaignId': 1341876198,
			'extensionType': 'CALLOUT',
			'xsi_type': 'CampaignExtensionSetting',
			'extensionSetting': {
				'extensions': [
					{
						'xsi_type': 'CalloutFeedItem',
						'calloutText': 'Clique aqui'
					},
					{
						'xsi_type': 'CalloutFeedItem',
						'calloutText': 'Somos Legais'
					},
					{
						'xsi_type': 'CalloutFeedItem',
						'calloutText': 'Contrate aqui'
					}
				]
			}
		},
		'operator': 'ADD',
		'xsi_type': 'CampaignExtensionSettingOperation'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_campaign_ad_schedule_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_ad_schedule',
		'client_id': 7857288943,
		'fields': ['CampaignId'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}

	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'ordering': [],
		 'paging': {
			 'numberResults': 10000,
			  'xsi_type': 'Paging',
			 'startIndex': 0
		 },
		'xsi_type': 'Selector',
		'fields': ['CampaignId'],
		'predicates': [{
			'field': 'CampaignId',
			'values': [213213123],
			'xsi_type': 'Predicate',
			'operator': 'EQUALS'
		},{
			'field': 'CriteriaType',
			'values': ['AD_SCHEDULE'],
			'xsi_type': 'Predicate',
			'operator': 'EQUALS'
		}]
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'campaign_ad_schedule',
		'client_id': 3434324334,
		'day_of_week': 'MONDAY',
		'start_hour': 8,
		'start_minute': 23,
		'end_hour': 9,
		'end_minute': 33,
		'bid_modifier': 0.3,
		'campaign_id': 3353453453,
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operand': {
			'criterion': {
				'endMinute': 33,
				'startMinute': 23,
				'xsi_type': 'AdSchedule',
				'endHour': 9,
				'dayOfWeek': 'MONDAY',
				'startHour': 8,
			},
			'xsi_type': 'CampaignCriterion',
			'bidModifier': 0.3,
			'campaignId': 3353453453
		},
		'xsi_type': 'CampaignCriterionOperation',
		'operator': 'ADD'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_get_campaign_criterion_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_language',
		'client_id': 9973876376,
		'fields': ['CampaignId', 'Id'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'fields': ['CampaignId', 'Id'],
		'ordering': [],
		'xsi_type': 'Selector',
		'predicates': [{
			'operator': 'EQUALS',
			'xsi_type': 'Predicate',
			'field': 'CampaignId',
			'values': [213213123]
		},{
			'operator': 'EQUALS',
			'xsi_type': 'Predicate',
			'field': 'CriteriaType',
			'values': ['LANGUAGE']
		}],
		'paging': {'startIndex': 0, 'numberResults': 10000, 'xsi_type': 'Paging'}
	}

	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	get_internal_operation = {
		'object_type': 'campaign_targeted_location',
		'client_id': 9973876376,
		'fields': ['CampaignId', 'Id'],
		'predicates': [
			('CampaignId', 'EQUALS', 213213123),
		]
	}
	expected_get_adwords_operation = {
		'fields': ['CampaignId', 'Id'],
		'ordering': [],
		'xsi_type': 'Selector',
		'predicates': [{
			'operator': 'EQUALS',
			'xsi_type': 'Predicate',
			'field': 'CampaignId',
			'values': [213213123]
		},{
			'operator': 'EQUALS',
			'xsi_type': 'Predicate',
			'field': 'CriteriaType',
			'values': ['LOCATION']
		}],
		'paging': {'startIndex': 0, 'numberResults': 10000, 'xsi_type': 'Paging'}
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))

	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation


def _build_shared_set_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'shared_set',
		'client_id': 7857288943,
		'fields': ['Name', 'SharedSetId', 'Type', 'Status'],
		'predicates': [
			('Name', 'EQUALS', 'API Sync Test'),
			('Status', 'EQUALS', 'ENABLED')
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'ordering': [],
		'predicates': [{
			'operator': 'EQUALS',
			'values': ['API Sync Test'],
			'xsi_type': 'Predicate',
			'field': 'Name'
		},{
			'operator': 'EQUALS',
			'values': ['ENABLED'],
			'xsi_type': 'Predicate',
			'field': 'Status'}
		],
		'xsi_type': 'Selector',
		'fields': ['Name', 'SharedSetId', 'Type', 'Status'],
		'paging': {'startIndex': 0, 'xsi_type': 'Paging', 'numberResults': 10000}
	}
	get_adwords_operation['predicates'] = sorted(get_adwords_operation['predicates'], key=lambda x: x['field'])
	expected_get_adwords_operation['predicates'] = sorted(
		expected_get_adwords_operation['predicates'], key=lambda x: x['field']
	)
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'shared_set',
		'client_id': 7857288943,
		'shared_set_name': 'API Sync Test',
		'shared_set_type': 'NEGATIVE_KEYWORDS',
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'xsi_type': 'SharedSetOperation',
		'operator': 'ADD',
		'operand': {
			'xsi_type': 'SharedSet',
			'name': 'API Sync Test',
			'type': 'NEGATIVE_KEYWORDS'
		}
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_campaign_shared_set_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_shared_set',
		'fields': ['CampaignId', 'SharedSetId'],
		'predicates': [
			('CampaignId', 'EQUALS', 35345353534),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'ordering': [],
		'fields': ['CampaignId', 'SharedSetId'],
		'xsi_type': 'Selector',
		'predicates': [{
			'operator': 'EQUALS',
			'xsi_type': 'Predicate',
			'values': [35345353534],
			'field': 'CampaignId'}],
		'paging': {'numberResults': 10000, 'xsi_type': 'Paging', 'startIndex': 0}}

	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

	mutate_internal_operation = {
		'object_type': 'campaign_shared_set',
		'client_id': 5543543543,
		'campaign_id': 455353535,
		'shared_set_id': 3453535545
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operand': {
			'xsi_type': 'CampaignSharedSet',
			'sharedSetId': 3453535545,
			'campaignId': 455353535
		},
		'xsi_type': 'CampaignSharedSetOperation',
		'operator': 'ADD'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_shared_criterion_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'shared_criterion',
		'fields': ['Id', 'SharedSetId'],
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	expected_get_adwords_operation = {
		'fields': ['Id', 'SharedSetId'],
		'xsi_type': 'Selector',
		'paging': {
			'xsi_type': 'Paging',
			'startIndex': 0,
			'numberResults': 10000
		},
		'ordering': [],
		'predicates': []
	}
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation


	mutate_internal_operation = {
		'object_type': 'shared_criterion',
		'client_id': 656565465,
		'is_negative': True,
		'criterion_type': 'Keyword',
		'match_type': 'EXACT',
		'keyword_text': 'Teste2',
		'shared_set_id': 5465465464
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'xsi_type': 'SharedCriterionOperation',
		'operand': {
			'criterion': {
				'text': 'Teste2',
				'xsi_type': 'Keyword',
				'matchType': 'EXACT'
			},
			'xsi_type': 'SharedCriterion',
			'negative': True,
			'sharedSetId': 5465465464
		},
		'operator': 'ADD'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_managed_customer_operations():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'managed_customer',
		'fields': ['Name', 'CustomerId'],
		'predicates': [
			('CustomerId', 'EQUALS', 35345353534),
		]
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))

	expected_get_adwords_operation = {
		'xsi_type': 'Selector',
		'predicates': [
			{
				'operator': 'EQUALS',
				'xsi_type': 'Predicate',
				'field': 'CustomerId',
				'values': [35345353534]
			}
		],
		'paging': {'startIndex': 0, 'xsi_type': 'Paging', 'numberResults': 10000},
		'fields': ['Name', 'CustomerId'],
		'ordering': []
	}
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation


	mutate_internal_operation = {
		'object_type': 'managed_customer',
		'name': 'Customer Name',
		'currency_code': 'BRL',
		'date_time_zone': 'America/Sao_Paulo'
	}

	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operand': {
			'currencyCode': 'BRL',
			'name': 'Customer Name',
			'dateTimeZone': 'America/Sao_Paulo'
		},
		'operator': 'ADD'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_attach_label_operations():
	operation_builder = OperationsBuilder()
	mutate_internal_operation = {
		'object_type': 'attach_label',
		'client_id': 9973876376,
		'campaign_id': 1341876198,
		'label_id': 34324324
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operator': 'ADD',
		'operand': {
			'labelId': 34324324,
			'campaignId': 1341876198
		},
		'xsi_type': 'CampaignLabelOperation'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation

	mutate_internal_operation = {
		'object_type': 'attach_label',
		'client_id': 9973876376,
		'ad_id': 3453454353,
		'label_id': 34324324
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operator': 'ADD',
		'operand': {
			'labelId': 34324324,
			'adId': 3453454353
		},
		'xsi_type': 'AdGroupAdLabelOperation'
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation

	mutate_internal_operation = {
		'object_type': 'attach_label',
		'client_id': 9973876376,
		'ad_group_id': 3453454353,
		'label_id': 34324324
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operator': 'ADD',
		'xsi_type': 'AdGroupLabelOperation',
		'operand': {
			'adGroupId': 3453454353,
			'labelId': 34324324}
	}
	assert expected_mutate_adwords_operation == mutate_adwords_operation

	mutate_internal_operation = {
		'object_type': 'attach_label',
		'client_id': 9973876376,
		'customer_id': 3453454353,
		'label_id': 34324324
	}
	mutate_adwords_operation = next(operation_builder(mutate_internal_operation, sync=True))
	expected_mutate_adwords_operation = {
		'operator': 'ADD', 'operand': {
		'labelId': 34324324,
		'customerId': 3453454353
		}
	 }
	assert expected_mutate_adwords_operation == mutate_adwords_operation


def _build_operations_with_default_fields():
	operation_builder = OperationsBuilder()
	get_internal_operation = {
		'object_type': 'campaign_ad_schedule',
		'client_id': 7857288943,
		'default_fields': True
	}
	get_adwords_operation = next(operation_builder(get_internal_operation, sync=True))
	get_adwords_operation['fields'] = set(get_adwords_operation['fields'])
	expected_get_adwords_operation = {
		 'paging': {
			 'startIndex': 0,
			 'xsi_type': 'Paging',
			 'numberResults': 10000
		},
		 'xsi_type': 'Selector',
		 'fields': ['StartHour', 'StartMinute', 'BidModifier', 'EndHour', 'DayOfWeek', 'EndMinute'],
		 'ordering': [],
		 'predicates': [{
			 'values': ['AD_SCHEDULE'],
			 'xsi_type': 'Predicate',
			 'operator': 'EQUALS',
			 'field': 'CriteriaType'
		 }]
	 }
	get_adwords_operation['fields'] = sorted(get_adwords_operation['fields'])
	expected_get_adwords_operation['fields'] = sorted(expected_get_adwords_operation['fields'])
	assert expected_get_adwords_operation == get_adwords_operation

def test_build_adwords_operations():
	_build_shared_set_operations()
	_build_budget_order_operations()
	_build_site_link_operations()
	_build_structured_snipppet_operations()
	_build_callout_operations()
	_build_campaign_ad_schedule_operations()
	_build_get_campaign_criterion_operations()
	_build_shared_set_operations()
	_build_campaign_shared_set_operations()
	_build_shared_criterion_operations()
	_build_managed_customer_operations()
	_build_attach_label_operations()
	_build_operations_with_default_fields()
	_build_campaign_ad_schedule_operations()


def test_client():
	_delete_campaigns()
	_create_campaign()
	_adjust_bids()
	_get_keywords_report()
	_delete_campaigns()
	_sync_operations()


def test_get_accounts():
	client = AdWords(workdir='./tests/generated_files')
	client.get_accounts()
