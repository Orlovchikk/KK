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

	if len(groups.Response.Items) < 1 {
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

	if len(wall.Response.Items) == 0 {
		return false, WallResponse{}
	}
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
	Success string          `json:"success"`
	Posts   map[string]Post `json:"posts"`
}

func finalMarshal(wall WallResponse, success string) ResultJSON {
	posts := make(map[string]Post)
	for i, post := range wall.Response.Items {
		posts[fmt.Sprintf("post%d", i+1)] = Post{
			Text: post.Text,
			Date: post.Date,
		}
	}

	resultJSON := ResultJSON{
		Success: success,
		Posts:   posts,
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
		return lastPart, nil
	} else {
		// Если это логин, запрашиваем ID через API
		return getUserID(lastPart, token)
	}
}

func ParseHandler(w http.ResponseWriter, r *http.Request) {
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
	defer r.Body.Close()
	loadEnv()

	// Получаем токен из .env
	token := os.Getenv("VK_ACCESS_TOKEN")
	if token == "" {
		log.Fatalf("VK_ACCESS_TOKEN not set in .env file")
	}
	userID, err := parseVKLink(req.Link, token)
	if err != nil {
		log.Fatal(err)
	}

	isPosts, posts := getPosts(userID, token)
	//isGroups, groups := getGroups(userID, token)
	var success string
	if isPosts {
		success = "Success receive data from account: " + userID
		log.Println("Success receive data from account: " + userID)
	} else {
		success = "Cannot receive data from account: " + userID
		log.Println("Cannot receive data from account: " + userID)
	}

	resultJSON := finalMarshal(posts, success)
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
	http.HandleFunc("/parse", ParseHandler)

	fmt.Println("Parser listening on port 8000")
	log.Fatal(http.ListenAndServe(":8000", nil))
}
