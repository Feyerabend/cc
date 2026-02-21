
// Context.java
// Set Lonnert, 1999

abstract class Node { }

class ListNode extends Node {
  Object value;
  Object key;
  ListNode prev, next;
  ListNode(Object _key, Object _value) {
    key = _key;
    value = _value;
  }
}

class LinkedList {
  ListNode head;

  boolean isEmpty() {
    return (head == null);
  }
  void insert(ListNode x) {
    x.next = head;
    if (head != null) {
      head.prev = x;
    }
    head = x;
    x.prev = null;
  }
  void delete(ListNode x) {
    if (x.prev != null) {
      x.prev.next = x.next;
    } else {
      head = x.next;
    }
    if (x.next != null) {
      x.next.prev = x.prev;
    }
  }
  void delete(Object k) {
    delete(searchNode(k));
  }
  ListNode searchNode(Object k) {
    ListNode z = head;
    while (z != null && !z.key.equals(k)) {
      z = z.next;
    }
    return z;
  }
  Object search(Object k) {
    ListNode z = searchNode(k);
    if (z != null) {
      return z.value;
    }
    return z;
  }
  void walk() {
    ListNode x = head;
    while (x != null) {
      System.out.println(" Key: " + x.key + ", Value: " + x.value);
      x = x.next;
    }
  }
}

public class Context {
  LinkedList b;
  Context() {
    b = new LinkedList();
  }
  public void assign(VariableExp n, int v) {
    b.insert(new ListNode(n.toString(), new Integer(v)));
  }
  public int lookup(String n) {
    return ((Integer) b.search(n)).intValue();
  }
}
