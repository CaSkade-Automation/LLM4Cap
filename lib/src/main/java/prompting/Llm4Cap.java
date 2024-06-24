package prompting;

import clients.LlmClient;
import clients.LlmClientFactory;
import clients.LlmModels;

public class Llm4Cap {

	public static String generateCapability(String capabilityDescription, LlmModels model) throws Exception {
		
		// Get a client depending on the model
		LlmClient client = LlmClientFactory.getClient(model);
		
		// Generate the capability and return the result 		
		String result = client.generateCapability(capabilityDescription);
		return result;
	} 
}
