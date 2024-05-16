package prompting;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class GPT4Prompting {
	private static final String API_URL = "https://api.openai.com/v1/chat/completions";

	public void gpt4Prompting(String nLCapDescription) {
		
		String prompt= PromptGeneration.generatePrompt(nLCapDescription);
		
		Properties prop = new Properties();
        try (InputStream input = GPT4Prompting.class.getClassLoader().getResourceAsStream("config.properties")) {
            if (input == null) {
                System.err.println("Unable to find config.properties");
                return;
            }
            prop.load(input);
        } catch (IOException ex) {
            ex.printStackTrace();
            return;
        }

        String apiKey = prop.getProperty("openai.api.key");
        if (apiKey == null || apiKey.trim().isEmpty()) {
            System.err.println("API key not found in config.properties");
            return;
        }
		
		try {
            OkHttpClient client = new OkHttpClient();
            MediaType mediaType = MediaType.parse("application/json");

            String jsonBody = "{"
                    + "\"model\": \"gpt-4o\","
                    + "\"messages\": [{\"role\": \"user\"," 
                    + "\"content\":" + prompt + "}],"
                    + "\"temperature\": 0"
                    + "}";

            RequestBody body = RequestBody.create(jsonBody, mediaType);
            Request request = new Request.Builder()
                    .url(API_URL)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .addHeader("Authorization", "Bearer " + apiKey)
                    .build();

            Response response = client.newCall(request).execute();
            if (response.isSuccessful() && response.body() != null) {
                String responseBody = response.body().string();
                System.out.println(responseBody);
            } else {
                System.err.println("Request failed: " + response.code());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
