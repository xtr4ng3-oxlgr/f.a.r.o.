# WhatsApp Web fix

FARO v5.1 uses WhatsApp Web first:

```text
https://web.whatsapp.com/send?phone=<number>&text=<message>
```

If that fails, it can fall back to:

```text
https://wa.me/<number>?text=<message>
```

The number must be international format:

- no plus sign;
- no spaces;
- no hyphens;
- no parentheses.

Argentina example:

```text
549291XXXXXXX
```

Contacts must be marked as `extreme` to receive critical protection alerts.
