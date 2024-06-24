package clients;

public class ClaudeClient extends LlmClient{
    
	public ClaudeClient(LlmModels model) {
		super(model);
		this.model = model;
	}
	
	@Override
    public String generateCapability(String prompt) {
        // Hier die Logik zur Kommunikation mit der Claude API
        return "Response from Claude API based on prompt: " + prompt;
    }
}
