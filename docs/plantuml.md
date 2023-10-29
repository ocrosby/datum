# Plant UML

Pull the PlantUML docker image:

```bash
docker pull plantuml/plantuml-server:jetty
```

Run the PlantUML Server Container

```bash
docker run -d -p 8081:8080 plantuml/plantuml-server:jetty
```

- -d : Runs the container in detached mode.
- -p : Maps the container port 8080 to the host port 8081

Once the container is running, you can access the PlantUML server in your browser by visiting http://localhost:8081


## References

- [PlantUML](http://plantuml.com/)