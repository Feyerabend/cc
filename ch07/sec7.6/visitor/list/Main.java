

abstract class Node {
  abstract Object accept(NodeVisitor ask);
}

class EmptyNode extends Node {

  Object accept(NodeVisitor ask) {
    return ask.forEmptyNode(this);
  }
}

class NextNode extends Node {
  Object t;
  Node n;
  NextNode(Object _t, Node _n) {
    t = _t;
    n = _n;
  }

  Object accept(NodeVisitor ask) {
    return ask.forNextNode(this);
  }
}

interface NodeVisitor {
  Object forEmptyNode(EmptyNode that);
  Object forNextNode(NextNode that);
}

class Remove implements NodeVisitor {
  Object o;
  Remove(Object _o) {
    o = _o;
  }

  public Object forEmptyNode(EmptyNode that) {
    return new EmptyNode();
  }
  public Object forNextNode(NextNode that) {
    if (o.equals(that.t)) {
      return that.n.accept(this);
    } else {
      return new NextNode(that.t, (Node) that.n.accept(this));
    }
  }
}

class Insert implements NodeVisitor {
  Object o;
  Insert(Object _o) {
    o = _o;
  }

  public Object forEmptyNode(EmptyNode that) {
    return new NextNode(o, new EmptyNode());
  }
  public Object forNextNode(NextNode that) {
    return new NextNode(that.t, (Node) that.n.accept(this));
  }
}

class Replace implements NodeVisitor {
  Object r;
  Object o;
  Replace(Object _r, Object _o) {
    r = _r;
    o = _o;
  }

  public Object forEmptyNode(EmptyNode that) {
    return new EmptyNode();
  }
  public Object forNextNode(NextNode that) {
    if (o.equals(that.t)) {
      return new NextNode(r, (Node) that.n.accept(this));
    } else {
      return new NextNode(that.t, (Node) that.n.accept(this));
    }
  }
}

class PrintElements implements NodeVisitor {

  public Object forEmptyNode(EmptyNode that) {
    System.out.println();
    return (Object) null;
  }
  public Object forNextNode(NextNode that) {
    System.out.println((Object) that.t);
    that.n.accept(this);
    return (Object) that.t;
  }
}


interface TreeDuties {
  void add(Object o);
  void insert(Object o);
  void remove(Object o);
  void replace(Object o, Object p);
}

class Gardener implements TreeDuties {
  Node t = new EmptyNode();
  public void add(Object o) {
    t = new NextNode(o, t);
  }
  public void insert(Object o) {
    t = (Node) t.accept(new Insert(o));
  }
  public void remove(Object o) {
    t = (Node) t.accept(new Remove(o));
  }
  public void replace(Object o, Object p) {
    t = (Node) t.accept(new Replace(o, p));
  }
  public Object printAllElements() {
    return (Object) t.accept(new PrintElements());
  }
}


public class Main {
  public static void main(String args[]) {
    Gardener g = new Gardener();
    g.add("1");
    g.add("2");
    g.add("3");
    g.add("4");
    g.add("5");
    g.add("6");
    g.insert("7");
    g.insert("8");
    g.add("9");
    g.printAllElements();
    g.replace("0", "1");
    g.printAllElements();
    g.replace("0", "1");
  }
}
