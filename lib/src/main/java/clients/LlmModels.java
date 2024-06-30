package clients;

/**
 * Enum holding all models. Enums cannot have "-", which is why this enum is built like a key-value pair
 */
public enum LlmModels {
		claude_3_5_sonnet_20240620("claude_3_5_sonnet_20240620"),
		claude_3_opus_20240229("claude_3_opus_20240229"),
		claude_3_sonnet_20240229("claude_3_sonnet_20240229"),
		claude_3_haiku_20240307("claude_3_haiku_20240307"),
		gpt_4o("gpt-4o"),
		gpt_4_turbo("gpt-4-turbo"),
		gpt_4("gpt-4"),
		gpt_3_5_turbo("gpt-3-5-turbo");
		
		private final String realName;

	    // Enum constructor
		LlmModels (String realName) {
	        this.realName = realName;
	    }

	    public String getRealName() {
	        return realName;
	    }
}
