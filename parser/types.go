package main

type Post struct {
	Text string `json:"text"`
	Date int64  `json:"date"`
}

type WallResponse struct {
	Response struct {
		Items []Post `json:"items"`
	} `json:"response"`
}

type GroupResponse struct {
	Response struct {
		Count int   `json:"count"`
		Items []int `json:"items"` // Список ID групп в виде чисел
	} `json:"response"`
}

type GroupInfo struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type GroupInfoResponse struct {
	Response []GroupInfo `json:"response"`
}
