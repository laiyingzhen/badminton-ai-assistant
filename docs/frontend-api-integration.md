# 前端 API 對接說明

本文件依目前後端程式碼整理，供前端工程師實作球拍推薦與對話式推薦功能。API 為 FastAPI，所有業務 API 皆使用 JSON，聊天目前不是串流回應。

## 1. 基本資訊

| 項目 | 開發環境設定 |
| --- | --- |
| Base URL | `http://127.0.0.1:8000` |
| API prefix | `/api/v1` |
| Content-Type | `application/json` |
| 認證 | 目前無 |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |

後端目前允許跨來源請求（CORS）。正式環境的 Base URL 應由環境變數提供，不要寫死在前端程式中。

建議設定：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

共用 fetch 包裝範例：

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const payload = data?.error ?? data?.detail;
    const error = new Error(
      payload?.message ?? `HTTP ${response.status}`,
    );
    Object.assign(error, {
      status: response.status,
      code: payload?.code,
      details: payload?.details,
      response: data,
    });
    throw error;
  }

  return data as T;
}
```

## 2. 共用資料定義

### 球員程度 `RacketLevel`

```ts
type RacketLevel = "beginner" | "intermediate" | "advanced";
```

| 值 | 建議顯示文字 |
| --- | --- |
| `beginner` | 初學者 |
| `intermediate` | 中階 |
| `advanced` | 進階 |

### 打法 `RacketPlayingStyle`

```ts
type RacketPlayingStyle = "offensive" | "defensive" | "all_round";
```

| 值 | 建議顯示文字 |
| --- | --- |
| `offensive` | 進攻型 |
| `defensive` | 防守型 |
| `all_round` | 全能型 |

### 品牌 `RacketBrand`

```ts
type RacketBrand = "YONEX" | "VICTOR" | "LI-NING" | "JNICE";
```

品牌值區分大小寫，前端必須傳上表中的固定值。品牌在推薦條件中為選填。

### 球拍資料 `RacketCandidate`

```ts
interface RacketCandidate {
  id: number;
  brand: string;
  model: string;
  price: string;              // Decimal 序列化後通常為字串，例如 "2990.00"
  distance: number | null;
  similarity: number | null;
}
```

- `price`：金額。建議前端保留原字串，需要顯示時再格式化，避免浮點誤差。
- `distance`：向量距離，越小越相近。
- `similarity`：目前後端以 `1 - distance` 計算，越大越相近。
- 前端主要展示 `brand`、`model`、`price`；距離及相似度可作除錯或輔助資訊，不應自行用它取代後端的最終推薦結果。

## 3. 健康檢查

### `GET /health`

用於確認 API server 是否啟動，不代表資料庫及 Gemini 服務一定可用。

成功回應 `200 OK`：

```json
{
  "status": "ok"
}
```

## 4. 一次性球拍推薦

### `POST /api/v1/recommendations/rackets`

使用完整條件直接取得一支推薦球拍。此端點適合表單式介面；若條件要透過自然語言逐步蒐集，請使用聊天 API。

Request body：

```ts
interface RacketRecommendationRequest {
  level: RacketLevel;
  playing_style: RacketPlayingStyle;
  budget: number | string; // 必須 > 0
  brand?: RacketBrand | null;
}
```

範例：

```http
POST /api/v1/recommendations/rackets
Content-Type: application/json

{
  "level": "intermediate",
  "playing_style": "offensive",
  "budget": 5000,
  "brand": "YONEX"
}
```

成功回應 `200 OK`：

```ts
interface RacketRecommendationResponse {
  racket: RacketCandidate;
  reason: string;
}
```

```json
{
  "racket": {
    "id": 1,
    "brand": "YONEX",
    "model": "ASTROX 7 DG",
    "price": "2990.00",
    "distance": 0.232582,
    "similarity": 0.767418
  },
  "reason": "此球拍符合你的程度、進攻打法與預算。"
}
```

可能狀態碼：

| HTTP | code | 說明 |
| --- | --- | --- |
| 200 | — | 推薦成功 |
| 404 | `NO_RACKET_CANDIDATE` | 預算及品牌條件內沒有候選球拍 |
| 422 | `VALIDATION_ERROR` | 欄位缺漏、列舉值錯誤或預算不大於 0 |
| 500 | `INVALID_RACKET_CANDIDATE` | AI 選到了候選清單以外的球拍 |
| 502 | `GEMINI_SERVICE_ERROR` | AI 服務失敗 |
| 503 | `DATABASE_SERVICE_ERROR` | 球拍資料庫查詢失敗 |

## 5. 對話式球拍推薦

### `POST /api/v1/recommendations/rackets/chat`

送出使用者自然語言訊息。第一次請求省略 `session_id`；後端會建立 session 並在回應中傳回 UUID。之後每次請求都必須帶回同一個 `session_id`，後端才會累積條件與對話。

Request body：

```ts
interface ChatRequest {
  message: string;       // 1～2000 個字元
  session_id?: string | null; // UUID
}
```

首次訊息：

```json
{
  "message": "我是中階進攻型球員，預算五千元"
}
```

後續訊息：

```json
{
  "message": "品牌希望是 YONEX",
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835"
}
```

Response：

```ts
type ChatStatus = "collecting" | "recommended" | "no_match";

interface ExtractedRacketCriteria {
  playing_style: RacketPlayingStyle | null;
  brand: RacketBrand | null;
  level: RacketLevel | null;
  budget: string | null;
}

interface ChatResponse {
  session_id: string;
  status: ChatStatus;
  message: string;
  criteria: ExtractedRacketCriteria;
  missing_fields: string[];
  recommendation: RacketCandidate | null;
}
```

`missing_fields` 目前可能包含：

- `playing_style`
- `level`
- `budget`

`brand` 不是必要條件，因此不會因品牌未提供而阻止推薦。

#### 狀態處理

| status | 意義 | 前端建議 |
| --- | --- | --- |
| `collecting` | 必填條件尚未齊全 | 顯示 `message` 作為 AI 追問；可依 `missing_fields` 提供快捷選項 |
| `recommended` | 已取得推薦 | 顯示 `message`、條件標籤及 `recommendation` 卡片 |
| `no_match` | 條件完整，但查無符合預算／品牌的球拍 | 顯示 `message`，引導使用者放寬預算或品牌；沿用 session 繼續傳新條件 |

蒐集中回應範例：

```json
{
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835",
  "status": "collecting",
  "message": "請問你的預算大約是多少？",
  "criteria": {
    "playing_style": "offensive",
    "brand": null,
    "level": "intermediate",
    "budget": null
  },
  "missing_fields": ["budget"],
  "recommendation": null
}
```

推薦成功回應範例：

```json
{
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835",
  "status": "recommended",
  "message": "推薦你 YONEX ASTROX 7 DG，價格 NT$ 2990。此球拍符合你的需求。",
  "criteria": {
    "playing_style": "offensive",
    "brand": "YONEX",
    "level": "intermediate",
    "budget": "5000.00"
  },
  "missing_fields": [],
  "recommendation": {
    "id": 1,
    "brand": "YONEX",
    "model": "ASTROX 7 DG",
    "price": "2990.00",
    "distance": 0.232582,
    "similarity": 0.767418
  }
}
```

注意：`message` 是 AI 產生或後端組合的顯示文字，不應由前端解析內容來判斷流程；流程一律以 `status`、`missing_fields`、`criteria` 與 `recommendation` 為準。

### Session 管理建議

1. 收到成功回應後立即保存 `session_id`（例如 state 加 `sessionStorage` 或 `localStorage`）。
2. 同一段對話的後續 POST 都帶上該值。
3. 使用者按「開始新對話」時，只需清除前端保存的 `session_id`；下一次省略它，後端即建立新 session。
4. 目前沒有刪除或重設 session 的 API。
5. 若後端回覆 `CHAT_SESSION_NOT_FOUND`，清除失效 ID，提示使用者對話已失效，下一則訊息改以新 session 送出。
6. 等待 POST 完成期間建議停用送出按鈕，避免同一 session 並行送出造成訊息順序或條件覆寫不確定。

## 6. 取得聊天紀錄

### `GET /api/v1/recommendations/rackets/chat/{session_id}/history`

`session_id` 必須是有效 UUID。回傳該 session 的目前條件與全部訊息，訊息依資料庫 ID 由小到大排列。目前沒有分頁。

```ts
type ChatRole = "user" | "assistant";

interface ChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  created_at: string; // ISO 8601 datetime
}

interface ChatHistoryResponse {
  session_id: string;
  criteria: ExtractedRacketCriteria;
  messages: ChatMessage[];
}
```

範例：

```json
{
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835",
  "criteria": {
    "playing_style": "offensive",
    "brand": null,
    "level": "intermediate",
    "budget": "5000.00"
  },
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "我是中階進攻型球員，預算五千元",
      "created_at": "2026-08-18T03:00:00+00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "推薦你 YONEX ASTROX 7 DG。",
      "created_at": "2026-08-18T03:00:02+00:00"
    }
  ]
}
```

前端顯示時間時，應以 `new Date(created_at)` 轉換成使用者本地時區。

## 7. 錯誤回應

目前後端存在兩種錯誤包裝格式，前端必須同時支援。

### 推薦服務與驗證錯誤：`error`

```ts
interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Array<{
      field: string;
      message: string;
    }>;
  };
}
```

422 範例：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "budget",
        "message": "Field required"
      }
    ]
  }
}
```

欄位位置可能是 `message`、`session_id`、`budget` 等；前端可用 `details[].field` 對應表單欄位。

### 聊天 session 不存在：`detail`

聊天 POST 或 history GET 使用不存在的 session 時，回覆 `404`：

```json
{
  "detail": {
    "code": "CHAT_SESSION_NOT_FOUND",
    "message": "Chat session b195cd65-f924-4db1-85c6-633ff3f25835 was not found."
  }
}
```

路徑中的 UUID 格式不合法則是 `422 VALIDATION_ERROR`，而不是 `CHAT_SESSION_NOT_FOUND`。

### 建議顯示策略

| 狀態 | 建議行為 |
| --- | --- |
| 400/422 | 顯示欄位錯誤，不要重試相同 payload |
| 404 session not found | 清除本地 session，提示開始新對話 |
| 404 no candidate | 顯示無符合商品並讓使用者調整條件 |
| 500 | 顯示一般系統錯誤，可提供重試 |
| 502/503 | 顯示服務暫時不可用，可稍後重試 |
| fetch 無 response | 視為網路、API URL 或 CORS 問題 |

## 8. 完整聊天串接範例

```ts
const CHAT_PATH = "/api/v1/recommendations/rackets/chat";
const SESSION_KEY = "racketChatSessionId";

async function sendChatMessage(message: string): Promise<ChatResponse> {
  const sessionId = localStorage.getItem(SESSION_KEY);

  const result = await apiFetch<ChatResponse>(CHAT_PATH, {
    method: "POST",
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
    }),
  });

  localStorage.setItem(SESSION_KEY, result.session_id);
  return result;
}

async function loadChatHistory(): Promise<ChatHistoryResponse | null> {
  const sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) return null;

  return apiFetch<ChatHistoryResponse>(
    `${CHAT_PATH}/${encodeURIComponent(sessionId)}/history`,
  );
}

function startNewChat(): void {
  localStorage.removeItem(SESSION_KEY);
}
```

## 9. 前端驗收清單

- Base URL 可依環境切換，路徑不重複 `/api/v1`。
- 所有 POST 都送出 `Content-Type: application/json`。
- 表單傳送的 enum 值與大小寫完全符合定義。
- `budget > 0`，聊天訊息長度為 1～2000。
- 聊天第一次不帶 `session_id`，之後保存並帶回 API 回覆的 UUID。
- UI 依 `status` 判斷流程，不解析 AI `message`。
- 正確處理 `recommendation: null` 及 criteria 中的 `null`。
- 金額能接受 JSON 字串，顯示時再做在地化格式。
- 錯誤解析同時支援 `error` 與 `detail` 包裝。
- history 的 UTC／時區時間能轉換為使用者本地時間。
- 請求期間防止重複送出，並提供 loading、網路錯誤及重試狀態。

## 10. 目前 API 限制

- 沒有登入或授權機制。
- 沒有聊天 session 刪除／重設端點。
- 聊天與 AI 回覆不是 SSE/WebSocket 串流，必須等待整個 JSON 回應。
- 聊天紀錄沒有分頁。
- 健康檢查只回報應用程式存活，未檢查資料庫與外部 AI 服務。
- 錯誤格式尚未完全統一；前端需依第 7 節相容處理。
