class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

    def has_next(self):
        return not (self.next is None)

    def has_prev(self):
        return not (self.prev is None)


class linked_list:
    def __init__(self):
        self.head = None
        self.size = 0

    # Adding data elements
    def append(self, newVal):
        newNode = Node(newVal)
        newNode.next = self.head
        if self.head is not None:
            self.head.prev = newNode
        self.head = newNode
        self.size += 1
        return newNode

    def remove(self, node):
        if node.has_prev():
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.has_next():
            node.next.prev = node.prev
        self.size -= 1

    def __iter__(self):
        return Linked_list_iterator(self)


class Linked_list_iterator:
    def __init__(self, l):
        self.l = l
        self.current = l.head

    def __next__(self):
        if self.current:
            result = self.current
            self.current = self.current.next
            return result.data
        raise StopIteration
