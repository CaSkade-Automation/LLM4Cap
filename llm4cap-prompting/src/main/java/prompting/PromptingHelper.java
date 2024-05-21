package prompting;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Request.Builder;
import okhttp3.RequestBody;
import okhttp3.Response;

public class PromptingHelper {

	static String loadApiKey(boolean gpt4o) throws Exception {
        try (InputStream input = PromptingHelper.class.getClassLoader().getResourceAsStream("config.properties")) {
            if (input == null) {
                System.err.println("Unable to find config.properties");
                throw new Exception("Not able to prompt gpt4 because of missing api-key");
            }
            Properties prop = new Properties();
            prop.load(input);
            
            String apiKey; 
            
            if (gpt4o) {
            	apiKey = prop.getProperty("openai.api.key");
            	if (apiKey == null || apiKey.trim().isEmpty()) {
            		System.err.println("API key not found in config.properties");
            		throw new Exception("Not able to prompt gpt4 because of missing api-key in config.properties");
            	}
            } else {
            	apiKey = prop.getProperty("x.api.key"); 
            	if (apiKey == null || apiKey.trim().isEmpty()) {
            		System.err.println("API key not found in config.properties");
            		throw new Exception("Not able to prompt gpt4 because of missing api-key in config.properties");
            	}
            }
            return apiKey;
        } catch (IOException e) {
        	e.printStackTrace();
        	throw new IOException(e.getCause()); 
        }
	}
	
	static Request buildRequest(boolean gpt4o, String prompt, String apiKey) {
        MediaType mediaType = MediaType.parse("application/json");
        
        String model; 
        String API_URL; 
        Builder requestBuilder = new Builder(); 
        
        if (gpt4o) {
        	model = "gpt-4o"; 
        	API_URL = "https://api.openai.com/v1/chat/completions";
        	requestBuilder.addHeader("Authorization", "Bearer " + apiKey); 
        } else {
        	model = "claude"; // TODO: needs to be replaced by real model name
        	API_URL = "https://api.anthropic.com/v1/messages"; 
        	requestBuilder.addHeader("x-api-key", apiKey)
        				.addHeader("anthropic-version", ""); // TODO add antrhopic version
        }
        String jsonBody = String.format("{"
            + "\"model\": \"%s\","
            + "\"messages\": [{\"role\": \"user\", \"content\": \"%s\"}],"
            + "\"temperature\": 0"
            + "}", model, prompt);

        RequestBody body = RequestBody.create(jsonBody, mediaType);
        return requestBuilder
                .url(API_URL)
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build();
    }
	
	static String promptLlm(OkHttpClient client, Request request) throws Exception {
		try (Response response = client.newCall(request).execute()) {
	        if (response.isSuccessful() && response.body() != null) {
	            String responseBody = response.body().string();
	            System.out.println(responseBody);
	            return responseBody; 
	        } else {
	            System.err.println("Request failed: " + response.code());
	            throw new Exception("Prompting gpt4 failed: " + response.code()); 
	        }
        } catch (IOException e) {
        	e.printStackTrace();
        	throw new IOException(e.getCause()); 
        }
	}
}
