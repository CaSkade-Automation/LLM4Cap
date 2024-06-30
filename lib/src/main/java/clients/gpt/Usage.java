package clients.gpt;

public class Usage {
    /**
     * The number of prompt tokens used.
     */
    long prompt_tokens;

    /**
     * The number of completion tokens used.
     */
    long completion_tokens;

    /**
     * The number of total tokens used
     */
    long total_tokens;
    
    public long getPromptTokens() {
    	return this.prompt_tokens;
    }
    
    public long getCompletionTokens() {
    	return this.completion_tokens;
    }
    
    public long getTotalTokens() {
    	return this.total_tokens;
    }
}