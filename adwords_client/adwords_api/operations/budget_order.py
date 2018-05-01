

def budget_order_operation(budget_order_id: 'Long' = None,
                           billing_account_id: 'Long' = None,
                           primary_billing_id: 'Long' = None,
                           start_date_time: 'String' = 'BRL',
                           end_date_time: 'String' = 'ADD',
                           spending_limit: 'Money' = None,
                           po_number: 'String' = None,
                           budget_order_name: 'String' = None,
                           operator: 'String' = 'ADD',
                               **kwargs):
    if not spending_limit:
        spending_limit = -1

    operation = {
        'operator': operator.upper(),
        'operand': {
            'billingAccountId': billing_account_id,
            'primaryBillingId': primary_billing_id,
            'startDateTime': start_date_time,
            'endDateTime': end_date_time,
            'spendingLimit':
                {
                    'microAmount': spending_limit
                }

        }
    }

    if budget_order_id:
        operation['operand']['id'] = budget_order_id
    if po_number:
        operation['operand']['poNumber'] = po_number
    if budget_order_name:
        operation['operand']['budgetOrderName'] = budget_order_name
    return operation
