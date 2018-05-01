from . import common as cm


class ManagedCustomerService(cm.BaseService):
    def __init__(self, client):
        super().__init__(client, 'ManagedCustomerService')

    def get_customers(self, client_customer_id=None, predicate=None):
        self.prepare_get()
        self.helper.add_fields('CustomerId', 'Name')
        if predicate:
            for predicate_item in predicate:
                self.helper.add_predicate(predicate_item['field'], predicate_item['operator'], predicate_item['values'])
        client_id = client_customer_id if client_customer_id else self.client.client_customer_id
        for customer in self.get(client_id):
            yield customer

    def update_managed_customer(self, operations, customer_id=None):
        self.prepare_mutate()
        self.helper.add_operations(operations)
        return self.mutate(customer_id)

    def mutate_accounts_labels(self, operations):
        return self.service.mutateLabel(operations)

    def cs_mutate(self, customer_id, operations):
        self.prepare_mutate()
        self.helper.add_operations(operations)
        return self.mutate(customer_id)

    def cs_mutate_labels(self, customer_id, operations):
        self.prepare_mutate()
        self.helper.add_operations(operations)
        return self.mutate_labels(customer_id)

    def cs_get(self, internal_operation):
        fields = ['CustomerId', 'Name']
        client_id = None
        self.prepare_get()
        if 'client_id' in internal_operation:
            client_id = internal_operation['client_id']
        if 'predicate' in internal_operation:
            for predicate_item in internal_operation['predicate']:
                self.helper.add_predicate(predicate_item['field'], predicate_item['operator'], predicate_item['values'])
        if 'fields' in internal_operation:
            [fields.append(field) for field in internal_operation['fields'] if field not in fields]
        self.helper.add_fields(*fields)
        return self.get(client_id)
