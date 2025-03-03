def declare_exchange_queues(channel):
    channel.exchange_declare(exchange='ArticleProcessing', exchange_type='topic', durable=True)

    channel.queue_declare(queue='extraction-tasks', durable=True)
    channel.queue_declare(queue='transformation-tasks', durable=True)
    
    channel.queue_bind(exchange='ArticleProcessing', queue='extraction-tasks', routing_key='extraction')
    channel.queue_bind(exchange='ArticleProcessing', queue='transformation-tasks', routing_key='transformation')

