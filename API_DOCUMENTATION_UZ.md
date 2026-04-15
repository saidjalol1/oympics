# Backend API Hujjatlari — Frontend Dasturchi Uchun

> Barcha so'rovlar `https://yourdomain.com` ga yuboriladi.
> Interaktiv hujjatlar: `https://yourdomain.com/docs`

---

## MUHIM: Autentifikatsiya qanday ishlaydi?

Backend **HttpOnly Cookie** ishlatadi. Ya'ni token JavaScript orqali o'qib bo'lmaydi — bu xavfsizlik uchun.

Login qilgandan so'ng server avtomatik `session` cookie o'rnatadi. Keyingi barcha so'rovlarda brauzer bu cookieni o'zi yuboradi.

**Frontend tomonidan qilish kerak bo'lgan narsa:**
```js
// credentials: 'include' — cookieni yuborish uchun MAJBURIY
fetch('https://yourdomain.com/api/auth/login', {
  method: 'POST',
  credentials: 'include',   // <-- BU MUHIM
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
```

> Barcha himoyalangan endpointlarda `credentials: 'include'` bo'lishi shart.

---

## 1. AUTENTIFIKATSIYA

### 1.1 Ro'yxatdan o'tish
```
POST /api/auth/register
```
**Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "kamida8belgi"
}
```
**Muvaffaqiyatli javob (201):**
```json
{
  "message": "Ro'yxatdan o'tish muvaffaqiyatli. Emailingizni tasdiqlang.",
  "user": null
}
```
**Xatolar:**
| Kod | Sabab |
|-----|-------|
| 400 | Email noto'g'ri yoki parol 8 belgidan kam |
| 409 | Bu email allaqachon ro'yxatdan o'tgan |
| 503 | Email xizmati ishlamayapti |

> Ro'yxatdan o'tgandan so'ng foydalanuvchi emailiga tasdiqlash havolasi yuboriladi.

---

### 1.2 Email tasdiqlash
```
GET /api/auth/verify?token=TOKEN&redirect_url=https://yoursite.com/dashboard
```
- `token` — emaildagi havoladan olinadi (majburiy)
- `redirect_url` — tasdiqlangandan keyin qayerga yo'naltirish (ixtiyoriy)

Agar `redirect_url` berilsa, foydalanuvchi o'sha sahifaga yo'naltiriladi va cookie o'rnatiladi.

---

### 1.3 Kirish (Login)
```
POST /api/auth/login
```
**Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "parol123"
}
```
**Muvaffaqiyatli javob (200):**
```json
{
  "message": "Kirish muvaffaqiyatli.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_verified": true,
    "is_admin": false,
    "created_at": "2026-04-15T10:00:00"
  }
}
```
> Server avtomatik `session` cookie o'rnatadi. Frontend hech narsa saqlashi shart emas.

**Xatolar:**
| Kod | Sabab |
|-----|-------|
| 401 | Email yoki parol noto'g'ri |
| 403 | Email tasdiqlanmagan |

---

### 1.4 Chiqish (Logout)
```
POST /api/auth/logout
```
Cookie o'chiriladi. Javob:
```json
{ "message": "Chiqish muvaffaqiyatli.", "user": null }
```

---

### 1.5 Token yangilash
```
POST /api/auth/refresh
```
Access token 15 daqiqada eskiradi. Shu endpoint orqali yangilanadi.
Cookie avtomatik yangilanadi.

---

### 1.6 Joriy foydalanuvchi ma'lumotlari
```
GET /api/auth/me
```
**Javob (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_verified": true,
  "is_admin": false,
  "created_at": "2026-04-15T10:00:00"
}
```
> 401 qaytsa — foydalanuvchi login qilmagan.

---

## 2. FANLAR VA DARAJALAR

### 2.1 Barcha fanlarni olish
```
GET /api/client/subjects
```
**Header:** `Accept-Language: uz` (yoki `en`, `ru`)

**Javob:**
```json
[
  { "id": 1, "name": "Matematika" },
  { "id": 2, "name": "Fizika" }
]
```

---

### 2.2 Fan bo'yicha darajalarni olish
```
GET /api/client/subjects/{subject_id}/levels
```
**Javob:**
```json
[
  { "id": 1, "name": "5-sinf" },
  { "id": 2, "name": "6-sinf" }
]
```

---

## 3. TESTLAR

### 3.1 Testlar ro'yxati (filter va pagination bilan)
```
GET /api/client/tests
```
**Query parametrlar (barchasi ixtiyoriy):**
| Parametr | Turi | Tavsif |
|----------|------|--------|
| `subject_id` | int | Fan bo'yicha filter |
| `level_id` | int | Daraja bo'yicha filter |
| `min_price` | float | Minimal narx |
| `max_price` | float | Maksimal narx |
| `skip` | int | Nechta o'tkazib yuborish (default: 0) |
| `limit` | int | Nechta qaytarish (default: 10, max: 100) |

**Javob:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Test 1",
      "price": 10.0,
      "level_id": 1,
      "level_name": "5-sinf",
      "subject_id": 1,
      "question_count": 10
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 10
}
```

---

### 3.2 Test savollarini olish (TO'LOV KERAK)
```
GET /api/client/tests/{test_id}
```
> **Autentifikatsiya majburiy.** Narxi > 0 bo'lgan testlar uchun avval to'lov qilingan bo'lishi kerak.

**Muvaffaqiyatli javob (200):**
```json
{
  "id": 1,
  "name": "Test 1",
  "price": 10.0,
  "level_id": 1,
  "level_name": "5-sinf",
  "subject_id": 1,
  "questions": [
    {
      "id": 1,
      "text": "2 + 2 = ?",
      "correct_answer": "A",
      "options": [
        { "id": 1, "label": "A", "text": "4" },
        { "id": 2, "label": "B", "text": "5" },
        { "id": 3, "label": "C", "text": "3" },
        { "id": 4, "label": "D", "text": "6" }
      ]
    }
  ]
}
```

**Xatolar:**
| Kod | Sabab |
|-----|-------|
| 401 | Login qilinmagan |
| 402 | To'lov qilinmagan |
| 404 | Test topilmadi |

---

### 3.3 Javoblarni yuborish
```
POST /api/client/tests/{test_id}/submit-answers
```
> Autentifikatsiya majburiy.

**Body (JSON):**
```json
{
  "answers": [
    { "question_id": 1, "answer": "A" },
    { "question_id": 2, "answer": "C" }
  ]
}
```
**Javob:**
```json
{
  "test_id": 1,
  "total_questions": 10,
  "correct_answers": 8,
  "score": 80,
  "results": [
    {
      "question_id": 1,
      "submitted_answer": "A",
      "correct_answer": "A",
      "is_correct": true
    }
  ]
}
```

---

## 4. TO'LOV (CLICK)

### To'lov jarayoni qanday ishlaydi?

```
Foydalanuvchi "To'lash" tugmasini bosadi
        ↓
POST /api/payment/initiate/{test_id}
        ↓
Backend payment_url qaytaradi
        ↓
Frontend foydalanuvchini payment_url ga yo'naltiradi (my.click.uz)
        ↓
Foydalanuvchi Click sahifasida to'laydi
        ↓
Click backend ga /prepare va /complete yuboradi (avtomatik)
        ↓
Frontend return_url ga qaytadi
        ↓
GET /api/payment/status/{test_id} — to'lov tasdiqlangan?
        ↓
Ha → GET /api/client/tests/{test_id} — savollarni ko'rsatish
```

---

### 4.1 To'lovni boshlash
```
POST /api/payment/initiate/{test_id}
```
> Autentifikatsiya majburiy.

**Javob (agar to'lov yangi):**
```json
{
  "payment_id": 1,
  "amount": 10.0,
  "payment_url": "https://my.click.uz/services/pay?service_id=99674&merchant_id=59143&amount=10.0&transaction_param=1&return_url=https://yoursite.com/tests/1"
}
```

**Javob (agar allaqachon to'langan):**
```json
{
  "status": "already_paid",
  "test_id": 1
}
```

**Frontend qilishi kerak:**
```js
const res = await fetch(`/api/payment/initiate/${testId}`, {
  method: 'POST',
  credentials: 'include'
})
const data = await res.json()

if (data.status === 'already_paid') {
  // Testni to'g'ridan-to'g'ri ochish
  router.push(`/tests/${testId}`)
} else {
  // Click sahifasiga yo'naltirish
  window.location.href = data.payment_url
}
```

---

### 4.2 To'lov holatini tekshirish
```
GET /api/payment/status/{test_id}
```
> Autentifikatsiya majburiy. Foydalanuvchi Click dan qaytgandan keyin chaqiriladi.

**Javob:**
```json
{ "test_id": 1, "paid": true }
```

**Frontend qilishi kerak (return_url sahifasida):**
```js
// Foydalanuvchi Click dan qaytgandan keyin
const res = await fetch(`/api/payment/status/${testId}`, {
  credentials: 'include'
})
const data = await res.json()

if (data.paid) {
  // Testni ochish
  router.push(`/tests/${testId}/questions`)
} else {
  // To'lov hali tasdiqlanmagan — biroz kutib qayta tekshirish
  setTimeout(checkStatus, 3000)
}
```

---

### 4.3 Prepare va Complete (FRONTEND UCHUN EMAS)
```
POST /api/payment/prepare   ← faqat Click serverlari chaqiradi
POST /api/payment/complete  ← faqat Click serverlari chaqiradi
```
Bu endpointlar Click tomonidan avtomatik chaqiriladi. Frontend bu endpointlarni chaqirmaydi.

---

## 5. TIL (LOCALIZATION)

Barcha endpointlar `Accept-Language` headerini qo'llab-quvvatlaydi:

```js
fetch('/api/client/subjects', {
  headers: { 'Accept-Language': 'uz' }  // yoki 'en', 'ru'
})
```

Qo'llab-quvvatlanadigan tillar: `uz`, `en`, `ru`. Default: `en`.

---

## 6. XATO KODLARI

| HTTP Kod | Ma'nosi |
|----------|---------|
| 200 | Muvaffaqiyatli |
| 201 | Yaratildi |
| 400 | Noto'g'ri so'rov (validatsiya xatosi) |
| 401 | Login qilinmagan |
| 402 | To'lov talab qilinadi |
| 403 | Ruxsat yo'q |
| 404 | Topilmadi |
| 409 | Allaqachon mavjud (masalan, email) |
| 500 | Server xatosi |

Xato javobi formati:
```json
{ "detail": "Xato tavsifi" }
```

---

## 7. CORS

Server hozirda barcha originlarga ruxsat beradi (`*`). Deploy qilgandan keyin frontend domenini aniq ko'rsatish tavsiya etiladi.

---

## 8. INTERAKTIV HUJJATLAR

Server ishga tushgandan keyin quyidagi manzilga kiring:
```
https://yourdomain.com/docs
```
U yerda barcha endpointlarni brauzerdan to'g'ridan-to'g'ri sinab ko'rish mumkin.
