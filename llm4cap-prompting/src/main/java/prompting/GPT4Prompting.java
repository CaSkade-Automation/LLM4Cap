package prompting;

import okhttp3.OkHttpClient;
import okhttp3.Request;

public class GPT4Prompting {

	public static String gpt4Prompting(String nLCapDescription) throws Exception {
		
		String prompt = PromptGeneration.generatePrompt(nLCapDescription);
		String apiKey = PromptingHelper.loadApiKey(true); 
		
        OkHttpClient client = new OkHttpClient();
        Request request = PromptingHelper.buildRequest(true, prompt, apiKey); 
        String response = PromptingHelper.promptLlm(client, request); 
        return response; 
	} 
}
