# 前端 API 對接說明

本文件依目前 FastAPI 後端與 `badminton_equipment_demo.html` 的實作整理，供前端工程師串接球拍條件查詢、文字／語音對話推薦及推薦球拍明細。

## 1. 基本資訊

| 項目 | 開發環境設定 |
| --- | --- |
| Base URL | `http://127.0.0.1:8000` |
| API prefix | `/api/v1` |
| 認證 | 目前無 |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |

後端目前允許跨來源請求（CORS）。正式前端應以環境變數提供 Base URL，不要將開發網址寫死：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

API 目前不是 SSE 或 WebSocket 串流；前端必須等待完整 JSON 回應。

## 2. API 一覽

| Method | Endpoint | Content-Type | 用途 |
| --- | --- | --- | --- |
| `GET` | `/health` | — | 應用程式健康檢查 |
| `GET` | `/api/v1/rackets` | — | 依條件查詢球拍清單 |
| `GET` | `/api/v1/rackets/{id}` | — | 取得單一球拍完整資料 |
| `POST` | `/api/v1/recommendations/rackets` | `application/json` | 以完整條件取得一次性推薦 |
| `POST` | `/api/v1/recommendations/rackets/chat` | `application/json` | 文字對話推薦 |
| `POST` | `/api/v1/recommendations/rackets/chat/voice` | `multipart/form-data` | 語音對話推薦 |
| `GET` | `/api/v1/recommendations/rackets/chat/{session_id}/history` | — | 取得聊天紀錄 |

## 3. 共用型別

```ts
export type RacketLevel =
  | "beginner"
  | "intermediate"
  | "advanced";

export type RacketPlayingStyle =
  | "offensive"
  | "defensive"
  | "all_round";

export type RacketBrand =
  | "YONEX"
  | "VICTOR"
  | "LI-NING"
  | "JNICE";

export type ChatStatus =
  | "collecting"
  | "recommended"
  | "no_match";
```

建議顯示文字：

| API 值 | 顯示文字 |
| --- | --- |
| `beginner` | 初學者 |
| `intermediate` | 中階 |
| `advanced` | 進階 |
| `offensive` | 進攻型 |
| `defensive` | 防守型 |
| `all_round` | 全能型 |

品牌 query 與 request body 的列舉值區分大小寫，例如必須傳 `YONEX`，不能傳 `Yonex`。

### 推薦候選球拍

聊天及一次性推薦回傳精簡候選資料：

```ts
export interface RacketCandidate {
  id: number;
  brand: string;
  model: string;
  price: string;
  distance: number | null;
  similarity: number | null;
}
```

### 完整球拍資料

球拍清單及單筆查詢回傳完整資料：

```ts
export interface RacketQueryResponse {
  id: number;
  brand: string;
  model: string;
  price: string;
  weight: string | null;
  balance: string | null;
  flexibility: string | null;
  suitable_level: string | null;
  playing_style: string | null;
  description: string | null;
  image_url: string | null;
  affiliate_url: string | null;
  is_active: boolean;
}

export interface RacketPaginationResponse {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export interface RacketListResponse {
  data: RacketQueryResponse[];
  pagination: RacketPaginationResponse;
}
```

Pydantic 的 `Decimal` 通常序列化為 JSON 字串，例如 `"2990.00"`。建議保留原字串，顯示時再格式化，避免浮點誤差。

## 4. 共用 fetch 與錯誤處理

後端錯誤可能包在 `error` 或 `detail`，前端必須同時支援。`FormData` 請勿自行設定 `Content-Type`，瀏覽器會自動加入 multipart boundary。

```ts
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: Array<{ field: string; message: string }>;
  response: unknown;

  constructor(
    message: string,
    status: number,
    payload: any,
    response: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = payload?.code;
    this.details = payload?.details;
    this.response = response;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const payload = data?.error ?? data?.detail;
    const message =
      typeof payload === "string"
        ? payload
        : payload?.message ?? `HTTP ${response.status}`;

    throw new ApiError(
      message,
      response.status,
      payload,
      data,
    );
  }

  return data as T;
}
```

## 5. 健康檢查

### `GET /health`

成功回應 `200 OK`：

```json
{
  "status": "ok"
}
```

此端點只表示 FastAPI 正常運作，不保證資料庫及 Gemini 可用。

## 6. 查詢球拍清單

### `GET /api/v1/rackets`

Query parameters：

| 欄位 | 必填 | 型別 | 規則 |
| --- | --- | --- | --- |
| `budget` | 是 | decimal | 必須大於 `0` |
| `playing_style` | 是 | `RacketPlayingStyle` | 固定列舉值 |
| `brand` | 否 | `RacketBrand` | 固定列舉值且區分大小寫 |
| `page` | 否 | integer | 預設 `1`，最小 `1` |
| `pageSize` | 否 | integer | 預設 `10`，範圍 `1～100` |

範例：

```http
GET /api/v1/rackets?budget=5000&playing_style=offensive&brand=YONEX&page=1&pageSize=20
```

```ts
export async function queryRackets(params: {
  budget: number | string;
  playingStyle: RacketPlayingStyle;
  brand?: RacketBrand | null;
  page?: number;
  pageSize?: number;
}): Promise<RacketListResponse> {
  const query = new URLSearchParams({
    budget: String(params.budget),
    playing_style: params.playingStyle,
    page: String(params.page ?? 1),
    pageSize: String(params.pageSize ?? 10),
  });

  if (params.brand) query.set("brand", params.brand);

  return apiFetch<RacketListResponse>(
    `/api/v1/rackets?${query.toString()}`,
  );
}
```

成功回應 `200 OK`：

```json
{
  "data": [
    {
      "id": 1,
      "brand": "YONEX",
      "model": "ASTROX 88 D PRO",
      "price": "4890.00",
      "weight": "4U",
      "balance": "head_heavy",
      "flexibility": "stiff",
      "suitable_level": "advanced",
      "playing_style": "offensive",
      "description": "適合後場進攻型選手。",
      "image_url": null,
      "affiliate_url": null,
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

## 7. 取得單一球拍

### `GET /api/v1/rackets/{id}`

`id` 必須是大於 `0` 的整數。成功回傳一筆 `RacketQueryResponse`。

```ts
export function getRacket(
  id: number,
): Promise<RacketQueryResponse> {
  return apiFetch<RacketQueryResponse>(
    `/api/v1/rackets/${encodeURIComponent(id)}`,
  );
}
```

找不到或球拍未啟用時回傳 `404`：

```json
{
  "detail": {
    "code": "RACKET_NOT_FOUND",
    "message": "Racket 999 was not found."
  }
}
```

### 推薦球拍連結串接方式

當聊天回應為 `recommended` 時，以 `recommendation.id` 建立可點擊的球拍名稱。點擊後呼叫單筆 API，再用回傳的完整資料更新篩選條件與結果區：

```ts
async function selectRecommendedRacket(
  recommendation: RacketCandidate,
): Promise<void> {
  const racket = await getRacket(recommendation.id);

  setFilters({
    playingStyle: racket.playing_style,
    budget: racket.price,
    brand: racket.brand,
  });

  setRackets([racket]);
}
```

此流程應呼叫 `GET /api/v1/rackets/{id}`。取得單筆資料後，不需要再自動呼叫 `GET /api/v1/rackets?...`。資料庫中的品牌顯示文字可能是 `Yonex`，若要再用於清單 query，必須先轉成後端接受的 `YONEX` 等列舉值。

## 8. 一次性球拍推薦

### `POST /api/v1/recommendations/rackets`

適合條件已完整的表單式推薦。自然語言與多輪對話請使用聊天 API。

```ts
export interface RacketRecommendationRequest {
  level: RacketLevel;
  playing_style: RacketPlayingStyle;
  budget: number | string;
  brand?: RacketBrand | null;
}

export interface RacketRecommendationResponse {
  racket: RacketCandidate;
  reason: string;
}
```

```ts
export function recommendRacket(
  request: RacketRecommendationRequest,
): Promise<RacketRecommendationResponse> {
  return apiFetch<RacketRecommendationResponse>(
    "/api/v1/recommendations/rackets",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}
```

Request 範例：

```json
{
  "level": "intermediate",
  "playing_style": "offensive",
  "budget": 5000,
  "brand": "YONEX"
}
```

## 9. 文字對話推薦

### `POST /api/v1/recommendations/rackets/chat`

```ts
export interface ExtractedRacketCriteria {
  playing_style: RacketPlayingStyle | null;
  brand: RacketBrand | null;
  level: RacketLevel | null;
  budget: string | null;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  session_id: string;
  status: ChatStatus;
  message: string;
  criteria: ExtractedRacketCriteria;
  missing_fields: string[];
  recommendation: RacketCandidate | null;
}
```

`message` 長度必須為 `1～2000`。第一次請求省略 `session_id`；後續對話必須傳回 API 提供的 UUID。

```ts
const CHAT_PATH = "/api/v1/recommendations/rackets/chat";
const SESSION_KEY = "racketChatSessionId";

export async function sendChatMessage(
  message: string,
): Promise<ChatResponse> {
  const sessionId = sessionStorage.getItem(SESSION_KEY);

  const result = await apiFetch<ChatResponse>(CHAT_PATH, {
    method: "POST",
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
    }),
  });

  sessionStorage.setItem(SESSION_KEY, result.session_id);
  return result;
}
```

前端應依結構化欄位控制 UI，不要解析 `message` 文字判斷流程：

| status | UI 建議 |
| --- | --- |
| `collecting` | 顯示 AI 追問，依 `missing_fields` 提示缺少條件 |
| `recommended` | 顯示訊息及 `recommendation` 球拍連結 |
| `no_match` | 顯示無符合商品，引導修改預算或品牌後沿用 session 對話 |

必要條件為 `playing_style`、`level`、`budget`；`brand` 為選填。

推薦成功範例：

```json
{
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835",
  "status": "recommended",
  "message": "推薦你選擇 YONEX ASTROX 7 DG，價格約 NT$ 2990。",
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

## 10. 語音對話推薦

### `POST /api/v1/recommendations/rackets/chat/voice`

Request 必須使用 `multipart/form-data`：

| Form 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `audio` | 是 | 錄音檔案，預設上限 10 MB |
| `session_id` | 否 | 後續對話使用的 UUID；第一次省略 |

支援 MIME type：MP3、MP4/M4A、WAV、WebM、OGG、FLAC。

```ts
export interface VoiceChatResponse extends ChatResponse {
  transcript: string;
}

export async function sendVoiceMessage(
  audio: Blob,
  filename = "recording.webm",
): Promise<VoiceChatResponse> {
  const formData = new FormData();
  formData.append("audio", audio, filename);

  const sessionId = sessionStorage.getItem(SESSION_KEY);
  if (sessionId) formData.append("session_id", sessionId);

  const result = await apiFetch<VoiceChatResponse>(
    `${CHAT_PATH}/voice`,
    {
      method: "POST",
      body: formData,
    },
  );

  sessionStorage.setItem(SESSION_KEY, result.session_id);
  return result;
}
```

不要手動設定 `Content-Type: multipart/form-data`，否則 request 可能缺少 boundary 而無法解析。

成功回應與 `ChatResponse` 相同，並多一個辨識結果：

```json
{
  "transcript": "我是初學者，喜歡全能型打法，預算三千元。",
  "session_id": "b195cd65-f924-4db1-85c6-633ff3f25835",
  "status": "recommended",
  "message": "推薦你選擇 YONEX ASTROX 7 DG。",
  "criteria": {
    "playing_style": "all_round",
    "brand": null,
    "level": "beginner",
    "budget": "3000.00"
  },
  "missing_fields": [],
  "recommendation": {
    "id": 1,
    "brand": "YONEX",
    "model": "ASTROX 7 DG",
    "price": "2990.00",
    "distance": 0.2,
    "similarity": 0.8
  }
}
```

## 11. 聊天紀錄與 Session 管理

### `GET /api/v1/recommendations/rackets/chat/{session_id}/history`

```ts
export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  criteria: ExtractedRacketCriteria;
  messages: ChatMessage[];
}

export async function loadChatHistory(): Promise<
  ChatHistoryResponse | null
> {
  const sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) return null;

  return apiFetch<ChatHistoryResponse>(
    `${CHAT_PATH}/${encodeURIComponent(sessionId)}/history`,
  );
}

export function startNewChat(): void {
  sessionStorage.removeItem(SESSION_KEY);
}
```

Session 使用原則：

1. 第一次文字或語音請求不帶 `session_id`。
2. 成功後立即保存回傳的 `session_id`。
3. 同一段對話的文字與語音請求共用同一個 ID。
4. 開始新對話時清除前端保存的 ID；後端目前沒有刪除 session API。
5. 收到 `CHAT_SESSION_NOT_FOUND` 時清除失效 ID，提示使用者開始新對話。
6. API 等待期間停用送出及錄音按鈕，避免同一 session 並行更新。

## 12. 錯誤格式與狀態碼

### `error` 包裝

驗證及服務層錯誤通常使用：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "brand",
        "message": "Input should be ..."
      }
    ]
  }
}
```

### `detail` 包裝

聊天 session、單筆球拍及語音檔案錯誤使用：

```json
{
  "detail": {
    "code": "RACKET_NOT_FOUND",
    "message": "Racket 999 was not found."
  }
}
```

常見狀態碼：

| HTTP | code | 說明 |
| --- | --- | --- |
| 400 | `EMPTY_AUDIO_FILE` | 語音檔案為空 |
| 404 | `NO_RACKET_CANDIDATE` | 找不到推薦候選球拍 |
| 404 | `RACKET_NOT_FOUND` | 找不到指定球拍或球拍未啟用 |
| 404 | `CHAT_SESSION_NOT_FOUND` | session 不存在 |
| 413 | `AUDIO_FILE_TOO_LARGE` | 語音檔超過後端限制 |
| 415 | `UNSUPPORTED_AUDIO_TYPE` | 不支援的音訊格式 |
| 422 | `VALIDATION_ERROR` | Request、query 或 path 驗證失敗 |
| 422 | `TRANSCRIPT_TOO_LONG` | 語音辨識結果超過 2000 字元 |
| 500 | `INVALID_RACKET_CANDIDATE` | AI 選到候選清單以外的 ID |
| 502 | `GEMINI_SERVICE_ERROR` | Gemini 或語音辨識失敗 |
| 503 | `DATABASE_SERVICE_ERROR` | 資料庫查詢失敗 |

## 13. 建議前端流程

```text
使用者輸入文字或錄音
        ↓
讀取已保存的 session_id
        ↓
POST /chat 或 POST /chat/voice
        ↓
保存回傳的 session_id
        ↓
依 status 顯示追問、無結果或推薦
        ↓
recommended：以 recommendation.id 建立球拍連結
        ↓
使用者點擊連結
        ↓
GET /api/v1/rackets/{id}
        ↓
以完整球拍資料更新篩選條件與結果區
```

## 14. 前端驗收清單

- Base URL 可依環境切換，且路徑不會重複 `/api/v1`。
- JSON POST 正確設定 `Content-Type: application/json`。
- 語音 POST 使用 `FormData`，不手動設定 `Content-Type`。
- enum 值及大小寫符合後端定義，尤其是品牌。
- `budget > 0`、訊息長度為 `1～2000`、`pageSize <= 100`。
- 第一次聊天不帶 `session_id`，後續文字與語音共用保存的 ID。
- UI 依 `status`、`missing_fields`、`criteria`、`recommendation` 判斷，不解析 AI 訊息。
- 正確處理 nullable 欄位及 Decimal 字串。
- 推薦球拍連結使用 `recommendation.id` 呼叫 `/rackets/{id}`。
- 錯誤解析同時支援 `error` 與 `detail`。
- 請求期間避免重複提交，並提供 loading、錯誤及重試狀態。
- `created_at` 使用 `new Date(created_at)` 轉換成使用者本地時間。

## 15. 目前限制

- 尚無登入及 API 授權機制。
- 聊天回應不是串流。
- 聊天紀錄沒有分頁。
- 沒有刪除或重設 session 的後端 API。
- 健康檢查不會檢查資料庫及 Gemini。
- 錯誤格式尚未統一，前端需相容 `error` 與 `detail`。
