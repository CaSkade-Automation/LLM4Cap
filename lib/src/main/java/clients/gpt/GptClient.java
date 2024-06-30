package clients;

import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpRequest.BodyPublishers;

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
		
		String prompt = PromptGeneration.generatePrompt(capabilityDescription);
		
		String jsonBody = String.format("{"
			    + "\"model\": \"%s\","
			    + "\"messages\": [{\"role\": \"user\", \"content\": \"%s\"}],"
			    + "\"temperature\": 0"
			    + "}", this.model, prompt);
		
    	HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(this.API_URL))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(BodyPublishers.ofString(jsonBody))
                .build();
    	
    	String result = executeRequest(request);
    	return result;
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
