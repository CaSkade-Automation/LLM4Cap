# LLM4Cap
Method for the automated generation of capability ontologies with LLMs and the verification of the results. 

## How to use?

### CLI 

First the application has to be compiled and packaged with: 
```
mvn clean package
```
In an IDE such as Eclipse a Maven Build can also be carried out with the Goal `package`. 

The CLI can then be used as follows:  
```
java -jar target/llm4cap-0.0.1-SNAPSHOT.jar "Here is the capability description."
```
or 
```
java -jar target/llm4cap-0.0.1-SNAPSHOT.jar -f CapabilityDescription.txt
```
