package main

import (
	"encoding/json"
	"fmt"
	"github.com/joho/godotenv"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
)

func loadEnv() {
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("Error loading .env file")
	}
}

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

func getGroupNames(groupIDs []int, token string) (bool, GroupInfoResponse) {
	ids := strings.Trim(strings.Replace(fmt.Sprint(groupIDs), " ", ",", -1), "[]")

	url := fmt.Sprintf("https://api.vk.com/method/groups.getById?group_ids=%s&access_token=%s&v=5.131", ids, token)
	resp, err := http.Get(url)
	if err != nil {
		fmt.Println("Error:", err)
		return false, GroupInfoResponse{}
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return false, GroupInfoResponse{}
	}

	// Выведем тело ответа для отладки
	//fmt.Println("Response body:", string(body))

	var groupInfo GroupInfoResponse
	err = json.Unmarshal(body, &groupInfo)
	if err != nil {
		fmt.Println("Error parsing JSON:", err)
		return false, GroupInfoResponse{}
	}

	//for _, group := range groupInfo.Response {
	//	fmt.Printf("Group: %s (ID: %d)\n", group.Name, group.ID)
	//}
	return true, groupInfo
}

func getGroups(userID, token string) (bool, GroupInfoResponse) {
	url := fmt.Sprintf("https://api.vk.com/method/groups.get?user_id=%s&access_token=%s&v=5.131", userID, token)
	resp, err := http.Get(url)
	if err != nil {
		fmt.Println("Error:", err)
		return false, GroupInfoResponse{}
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return false, GroupInfoResponse{}
	}

	//fmt.Println("Response body:", string(body)) // Добавляем вывод ответа для отладки

	var groups GroupResponse
	err = json.Unmarshal(body, &groups)
	if err != nil {
		fmt.Println("Error parsing JSON:", err)
		return false, GroupInfoResponse{}
	}

	isGet, names := getGroupNames(groups.Response.Items, token)
	if isGet {
		return true, names
	}
	return false, GroupInfoResponse{}
}

func getPosts(userID, token string) (bool, WallResponse) {
	url := fmt.Sprintf("https://api.vk.com/method/wall.get?owner_id=%s&count=5&access_token=%s&v=5.131", userID, token)
	resp, err := http.Get(url)
	if err != nil {
		fmt.Println("Error:", err)
		return false, WallResponse{}
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return false, WallResponse{}
	}

	var wall WallResponse
	err = json.Unmarshal(body, &wall)
	if err != nil {
		fmt.Println("Error parsing JSON:", err)
		return false, WallResponse{}
	}

	//for i, post := range wall.Response.Items {
	//	fmt.Printf("Post %d: %s (Date: %d)\n", i+1, post.Text, post.Date)
	//}
	return true, wall
}

type User struct {
	ID int `json:"id"`
}

type UsersResponse struct {
	Response []User `json:"response"`
}

func getUserID(username, token string) (string, error) {
	url := fmt.Sprintf("https://api.vk.com/method/users.get?user_ids=%s&access_token=%s&v=5.131", username, token)

	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	var usersResponse UsersResponse
	err = json.Unmarshal(body, &usersResponse)
	if err != nil {
		return "", err
	}

	if len(usersResponse.Response) == 0 {
		return "", fmt.Errorf("user not found")
	}

	return fmt.Sprintf("%d", usersResponse.Response[0].ID), nil
}

type ResultJSON struct {
	Success       bool            `json:"success"`
	Posts         map[string]Post `json:"posts"`
	Subscriptions []string        `json:"subscriptions"`
}

func finalMarshal(subscriptions GroupInfoResponse, wall WallResponse, success bool) ResultJSON {
	posts := make(map[string]Post)
	for i, post := range wall.Response.Items {
		posts[fmt.Sprintf("post%d", i+1)] = Post{
			Text: post.Text,
			Date: post.Date,
		}
	}

	subs := make([]string, len(subscriptions.Response))

	for i, groupID := range subscriptions.Response {
		subs[i] = groupID.Name + ","
	}
	resultJSON := ResultJSON{
		Success:       success,
		Posts:         posts,
		Subscriptions: subs,
	}
	return resultJSON
}

func parseVKLink(vkURL string, token string) (string, error) {
	// Разбираем URL
	u, err := url.Parse(vkURL)
	if err != nil {
		return "", err
	}

	// Получаем последний сегмент пути (логин или ID)
	pathParts := strings.Split(u.Path, "/")
	lastPart := pathParts[len(pathParts)-1]

	// Проверяем, является ли последний сегмент числом (ID)
	isID, err := regexp.MatchString(`^\d+$`, lastPart)
	if err != nil {
		return "", err
	}

	if isID {
		// Если это числовой ID, просто преобразуем его в int
		var userID int
		fmt.Sscanf(lastPart, "%d", &userID)
		return string(userID), nil
	} else {
		// Если это логин, запрашиваем ID через API
		return getUserID(lastPart, token)
	}
}

type ParseRequest struct {
	Link string `json:"link"`
}

type ParseResponse struct {
	Result string `json:"result"`
}

func parseHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ParseRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	loadEnv()
	token := os.Getenv("VK_ACCESS_TOKEN")
	if token == "" {
		http.Error(w, "VK_ACCESS_TOKEN not set", http.StatusInternalServerError)
		return
	}
	userID, err := parseVKLink(req.Link, token)

	if err != nil {
		http.Error(w, fmt.Sprintf("Error parsing VK link: %v", err), http.StatusBadRequest)
		return
	}

	isPosts, posts := getPosts(userID, token)
	isGroups, groups := getGroups(userID, token)
	success := isPosts && isGroups

	resultJSON := finalMarshal(groups, posts, success)

	resultJSONStr, err := json.Marshal(resultJSON)

	if err != nil {
		http.Error(w, "Error encoding JSON", http.StatusInternalServerError)
		return
	}

	response := ParseResponse{Result: string(resultJSONStr)}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	loadEnv()

	http.HandleFunc("/parse", parseHandler)

	fmt.Println("Parser listening on port 8000")
	log.Fatal(http.ListenAndServe(":8000", nil))
}
