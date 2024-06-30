package clients.gpt;

import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpRequest.BodyPublishers;

import com.google.gson.Gson;

import clients.LlmClient;
import clients.LlmModels;
import prompting.PromptGeneration;

public class GptClient extends LlmClient {

	final String API_KEY_NAME = "OPEN_AI_KEY";
	final String API_URL = "https://api.openai.com/v1/chat/completions";
	
    public GptClient(LlmModels model) {
		super(model);
		// TODO Auto-generated constructor stub
	}
	
	@Override
    public String generateCapability(String capabilityDescription) {
    	
		String apiKey = null; 
		try {
			apiKey = this.loadApiKey(this.API_KEY_NAME);
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		// Generate the complete prompt with all examples etc
		String prompt = PromptGeneration.generatePrompt(capabilityDescription);
		
		// Create a new GPT request object and serialize to JSON
		GptRequest gptRequest = new GptRequest();
		gptRequest.setTemperature(0);
		gptRequest.setModel(model);
		
		Message capabilityDescriptionMessage = new Message();
		capabilityDescriptionMessage.setRole("user");
		capabilityDescriptionMessage.setContent(prompt);
		
		gptRequest.addMessage(capabilityDescriptionMessage);
		
		Gson gson = new Gson();
		String requestBody = gson.toJson(gptRequest);
		
    	HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(this.API_URL))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(BodyPublishers.ofString(requestBody))
                .build();
    	
    	String result = executeRequest(request);
    	// Unwrap content:
    	ChatCompletionResult res = gson.fromJson(result, ChatCompletionResult.class);
    	return res.choices.get(0).message.getContent();
    }
}

//
//if (gpt4o) {
//	model = "gpt-4o"; 
//	API_URL = "https://api.openai.com/v1/chat/completions";
//	requestBuilder.addHeader("Authorization", "Bearer " + apiKey); 
//} else {
//	model = "claude"; // TODO: needs to be replaced by real model name
//	API_URL = "https://api.anthropic.com/v1/messages"; 
//	requestBuilder.addHeader("x-api-key", apiKey)
//				.addHeader("anthropic-version", ""); // TODO add antrhopic version
//}
//
//
//RequestBody body = RequestBody.create(jsonBody, mediaType);
//return requestBuilder
//        .url(API_URL)
//        .post(body)
//        .addHeader("Content-Type", "application/json")
//        .build();
