
## RSA and Diffie-Hellman

Instead of illustrating the two parts in secure communication in Micropython,
we look at them in the full Python version. You may adopt and test further
on the Raspberry Pi Pico yourself, as a project.

__RSA__ is used whenever you want a person or a system to have a long-term identity
that others can trust. It is typically generated once and kept for a long time.
The public part is published, the private part is kept secret. With RSA you can
encrypt small pieces of data for someone without having shared anything beforehand,
and you can create digital signatures that prove authenticity and integrity.
This is why RSA appears in certificates, software signing, secure email, and
authentication protocols.
It answers the question: “How can anyone talk securely to me, and how can I prove that I am really me?”

In practice RSA is used at the beginning of a secure connection, not for the whole
communication. A browser uses RSA to verify the identity of a server and to protect
the initial secrets that will be used later. It is chosen because it gives a stable,
verifiable identity and because public keys can be distributed freely without danger.

__Diffie–Hellman__ is used whenever two parties want to create a fresh secret for a
conversation without having met before and without storing anything long-term.
It is used at the start of a session to produce a shared key that only exists for
that session. This key is then used with fast symmetric encryption to protect all data.
Diffie–Hellman answers the question: “How can we create a secret together over a public network?”

It is used in HTTPS, SSH, VPNs, and messaging systems because it creates new secrets
every time. Even if an attacker records traffic today and steals a key tomorrow, old
conversations remain safe. That property is why Diffie–Hellman is preferred for session setup.

![Diffie-Hellman](./../../../../assets/image/secure/diffie.png)


#### Typical real-world flow:

When you connect to a website:

1. RSA (or another signature scheme) is used to prove the server’s identity.
2. Diffie–Hellman is used to agree on a shared session key.
3. Symmetric encryption uses that key to protect all communication.

So in daily use:

__RSA__ is about:

* identity
* trust
* authentication
* protecting small critical secrets
* signatures

__Diffie–Hellman__ is about:

* creating temporary secrets
* securing sessions
* privacy of conversations
* forward secrecy

Both are used to remove the need for pre-shared secrets and
typically to make large-scale secure communication possible on the internet.

