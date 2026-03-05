abstract class Node<T> {
  abstract Node<T> accept(NodeVisitor<T> ask);
}

class EmptyNode<T> extends Node<T> {

  @Override
  Node<T> accept(NodeVisitor<T> ask) {
    return ask.forEmptyNode(this);
  }
}

class NextNode<T> extends Node<T> {
  T t;
  Node<T> n;

  NextNode(T _t, Node<T> _n) {
    t = _t;
    n = _n;
  }

  @Override
  Node<T> accept(NodeVisitor<T> ask) {
    return ask.forNextNode(this);
  }
}

interface NodeVisitor<T> {
  Node<T> forEmptyNode(EmptyNode<T> that);
  Node<T> forNextNode(NextNode<T> that);
}

class Remove<T> implements NodeVisitor<T> {
  T o;

  Remove(T _o) {
    o = _o;
  }

  @Override
  public Node<T> forEmptyNode(EmptyNode<T> that) {
    return new EmptyNode<>();
  }

  @Override
  public Node<T> forNextNode(NextNode<T> that) {
    if (o.equals(that.t)) {
      return that.n.accept(this);
    } else {
      return new NextNode<>(that.t, that.n.accept(this));
    }
  }
}

class Insert<T> implements NodeVisitor<T> {
  T o;

  Insert(T _o) {
    o = _o;
  }

  @Override
  public Node<T> forEmptyNode(EmptyNode<T> that) {
    return new NextNode<>(o, new EmptyNode<>());
  }

  @Override
  public Node<T> forNextNode(NextNode<T> that) {
    return new NextNode<>(that.t, that.n.accept(this));
  }
}

class Replace<T> implements NodeVisitor<T> {
  T r;
  T o;

  Replace(T _r, T _o) {
    r = _r;
    o = _o;
  }

  @Override
  public Node<T> forEmptyNode(EmptyNode<T> that) {
    return new EmptyNode<>();
  }

  @Override
  public Node<T> forNextNode(NextNode<T> that) {
    if (o.equals(that.t)) {
      return new NextNode<>(r, that.n.accept(this));
    } else {
      return new NextNode<>(that.t, that.n.accept(this));
    }
  }
}

class PrintElements<T> implements NodeVisitor<T> {

  @Override
  public Node<T> forEmptyNode(EmptyNode<T> that) {
    System.out.println();
    return that;
  }

  @Override
  public Node<T> forNextNode(NextNode<T> that) {
    System.out.println(that.t);
    that.n.accept(this);
    return that;
  }
}

interface TreeDuties<T> {
  void add(T o);
  void insert(T o);
  void remove(T o);
  void replace(T o, T p);
}

class Gardener<T> implements TreeDuties<T> {
  Node<T> t = new EmptyNode<>();

  @Override
  public void add(T o) {
    t = new NextNode<>(o, t);
  }

  @Override
  public void insert(T o) {
    t = t.accept(new Insert<>(o));
  }

  @Override
  public void remove(T o) {
    t = t.accept(new Remove<>(o));
  }

  @Override
  public void replace(T o, T p) {
    t = t.accept(new Replace<>(o, p));
  }

  public Node<T> printAllElements() {
    return t.accept(new PrintElements<>());
  }
}

public class MainGen {
  public static void main(String[] args) {
    Gardener<String> g = new Gardener<>();

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
  }
}
